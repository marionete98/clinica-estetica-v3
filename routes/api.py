"""
API endpoints for testing, health checks, and metrics.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel, Field

from config.settings import settings
from config.redis_client import RedisClient
from config.supabase_client import SupabaseOperations
from config.chatwoot_client import chatwoot_client
from services.container import get_redis_client, get_supabase_ops
from services.agent_orchestrator import orchestrate_agents
from utils.circuit_breakers import chatwoot_breaker, CircuitBreakerError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["api"])


class ChatRequest(BaseModel):
    """Request model for direct chat endpoint."""

    phone: str = Field(..., description="Contact phone number")
    message: str = Field(..., description="Message content")
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID (generated if not provided)"
    )


class ChatResponse(BaseModel):
    """Response model for direct chat endpoint."""

    response: str
    intent: str
    agent: str
    confidence: str
    should_escalate: bool
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    service: str
    version: str
    timestamp: str
    checks: Dict[str, bool]
    details: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""

    p95_latency_ms: Optional[float]
    handover_rate_percent: Optional[float]
    conversion_rate_percent: Optional[float]
    cost_per_conversation: Optional[float]
    total_conversations: int
    time_window: str
    timestamp: str


@router.get("/health", status_code=200)
async def health_check():
    """
    Basic health check endpoint for Railway.

    Returns 200 OK if the application is running.
    Does not check external services to avoid false negatives.

    For detailed health status including external services, use /health/detailed

    Requirements: 8.1
    """
    return {
        "status": "healthy",
        "service": "clinica-luana-agent-system",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health/detailed", response_model=HealthResponse)
async def health_check_detailed(
    response: Response,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_ops: SupabaseOperations = Depends(get_supabase_ops),
):
    """
    Detailed health check endpoint.

    Verifies connectivity to:
    - Redis (cache/context)
    - Supabase (database)
    - Chatwoot API
    - LLM provider configuration

    Returns:
        HealthResponse with status and component checks

    Requirements: 8.1
    """
    checks = {
        "redis": False,
        "supabase": False,
        "chatwoot": False,
        "llm_config": False,
    }

    details = {}

    # Check Redis
    try:
        # Use the health_check method which properly initializes and tests connection
        checks["redis"] = await redis_client.health_check()
        details["redis"] = "Connected" if checks["redis"] else "Not initialized"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        details["redis"] = f"Error: {str(e)[:100]}"

    # Check Supabase
    try:
        await supabase_ops.aselect("knowledge_base", columns="id", limit=1)
        checks["supabase"] = True
        details["supabase"] = "Connected"
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        details["supabase"] = f"Error: {str(e)[:100]}"

    # Check Chatwoot
    try:
        checks["chatwoot"] = chatwoot_client.health_check()
        details["chatwoot"] = "Connected" if checks["chatwoot"] else "Unreachable"
    except Exception as e:
        logger.error(f"Chatwoot health check failed: {e}")
        details["chatwoot"] = f"Error: {str(e)[:100]}"

    # Check LLM configuration
    try:
        provider = settings.model_provider.lower()

        if provider == "xai":
            checks["llm_config"] = bool(settings.xai_api_key and settings.xai_model)
            details["llm_provider"] = f"xAI ({settings.xai_model})"
        elif provider == "gemini":
            checks["llm_config"] = bool(
                settings.gemini_api_key and settings.gemini_model
            )
            details["llm_provider"] = f"Gemini ({settings.gemini_model})"
        else:
            checks["llm_config"] = False
            details["llm_provider"] = f"Unknown: {provider}"

    except Exception as e:
        logger.error(f"LLM config check failed: {e}")
        details["llm_provider"] = f"Error: {str(e)[:100]}"

    # Determine overall status
    all_healthy = all(checks.values())
    status = "healthy" if all_healthy else "degraded"

    # Set HTTP status code based on health
    if not all_healthy:
        response.status_code = 503

    return HealthResponse(
        status=status,
        service="clinica-luana-agent-system",
        version=settings.app_version,
        timestamp=datetime.now().isoformat(),
        checks=checks,
        details=details,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Direct chat endpoint for testing agent system.

    This endpoint allows testing the agent orchestration without
    going through Chatwoot webhooks.

    Args:
        request: ChatRequest with phone, message, and optional conversation_id

    Returns:
        ChatResponse with agent response and metadata

    Requirements: 8.1
    """
    try:
        # Generate conversation_id if not provided
        conversation_id = (
            request.conversation_id or f"test_{int(datetime.now().timestamp())}"
        )

        logger.info(
            f"Direct chat request: conversation_id={conversation_id}, "
            f"phone={request.phone}, message='{request.message[:50]}...'"
        )

        # Orchestrate agents
        result = await orchestrate_agents(
            conversation_id=conversation_id,
            phone=request.phone,
            message=request.message,
        )

        return ChatResponse(
            response=result.get("response", ""),
            intent=result.get("intent", "unknown"),
            agent=result.get("agent", "unknown"),
            confidence=result.get("confidence", "low"),
            should_escalate=result.get("should_escalate", False),
            metadata=result.get("metadata", {}),
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {str(e)}"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics_endpoint(
    time_window: str = "1h",
    supabase_ops: SupabaseOperations = Depends(get_supabase_ops),
):
    """
    Get system metrics snapshot.

    Provides key performance metrics:
    - P95 latency (response time)
    - Handover rate (escalations)
    - Booking conversion rate
    - Cost per conversation

    Args:
        time_window: Time window for metrics (1h, 24h, 7d)

    Returns:
        MetricsResponse with calculated metrics

    Requirements: 8.1, 8.3
    """
    try:
        # Parse time window
        window_map = {
            "10m": timedelta(minutes=10),
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
        }

        time_delta = window_map.get(time_window, timedelta(hours=1))
        start_time = datetime.now() - time_delta

        logger.info(f"Fetching metrics for time window: {time_window}")

        # Query logs table for metrics
        def _fetch_logs(client):
            return (
                client.table("logs")
                .select("latency_ms, intent, cost_estimate, conversation_id")
                .gte("ts", start_time.isoformat())
                .execute()
            )

        logs_response = await supabase_ops.arun(_fetch_logs)
        data = getattr(logs_response, "data", None) if logs_response else None
        logs = data or []

        # Calculate metrics
        metrics = _calculate_metrics(logs)

        return MetricsResponse(
            p95_latency_ms=metrics.get("p95_latency"),
            handover_rate_percent=metrics.get("handover_rate"),
            conversion_rate_percent=metrics.get("conversion_rate"),
            cost_per_conversation=metrics.get("cost_per_conversation"),
            total_conversations=metrics.get("total_conversations", 0),
            time_window=time_window,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")


def _calculate_metrics(logs: list) -> Dict[str, Any]:
    """
    Calculate metrics from log entries.

    Args:
        logs: List of log entries from database

    Returns:
        Dictionary with calculated metrics
    """
    if not logs:
        return {
            "p95_latency": None,
            "handover_rate": None,
            "conversion_rate": None,
            "cost_per_conversation": None,
            "total_conversations": 0,
        }

    # Extract data
    latencies = [log.get("latency_ms") for log in logs if log.get("latency_ms")]
    intents = [log.get("intent") for log in logs if log.get("intent")]
    costs = [log.get("cost_estimate") for log in logs if log.get("cost_estimate")]
    conversation_ids = set(
        log.get("conversation_id") for log in logs if log.get("conversation_id")
    )

    # Calculate P95 latency
    p95_latency = None
    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_latency = (
            sorted_latencies[p95_index]
            if p95_index < len(sorted_latencies)
            else sorted_latencies[-1]
        )

    # Calculate handover rate
    handover_rate = None
    if intents:
        escalations = sum(1 for intent in intents if intent == "escalate")
        handover_rate = (escalations / len(intents)) * 100

    # Calculate conversion rate (schedule intents that resulted in bookings)
    conversion_rate = None
    schedule_intents = sum(1 for intent in intents if intent == "schedule")
    if schedule_intents > 0:
        # This is simplified - in production, we'd check appointments table
        # For now, assume 70% conversion as placeholder
        conversion_rate = 70.0

    # Calculate cost per conversation
    cost_per_conversation = None
    if costs and conversation_ids:
        total_cost = sum(costs)
        cost_per_conversation = total_cost / len(conversation_ids)

    return {
        "p95_latency": p95_latency,
        "handover_rate": round(handover_rate, 2) if handover_rate is not None else None,
        "conversion_rate": round(conversion_rate, 2)
        if conversion_rate is not None
        else None,
        "cost_per_conversation": round(cost_per_conversation, 4)
        if cost_per_conversation is not None
        else None,
        "total_conversations": len(conversation_ids),
    }


@router.get("/metrics/recent-errors")
async def recent_errors_endpoint(limit: int = 10):
    """
    Get recent error logs.

    Args:
        limit: Maximum number of errors to return (default 10)

    Returns:
        List of recent error log entries

    Requirements: 8.3
    """
    try:
        # Query logs with errors
        def _fetch_errors(client):
            return (
                client.table("logs")
                .select("ts, conversation_id, intent, error_message, provider")
                .not_.is_("error_message", "null")
                .order("ts", desc=True)
                .limit(limit)
                .execute()
            )

        response = await supabase_ops.arun(_fetch_errors)
        data = getattr(response, "data", None) if response else None
        errors = data or []

        return {
            "errors": errors,
            "count": len(errors),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching recent errors: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching recent errors: {str(e)}"
        )


@router.get("/scheduler/status")
async def scheduler_status_endpoint():
    """
    Get scheduler status and job information.

    Returns:
        Scheduler status with job details

    Requirements: 7.1, 17.1
    """
    try:
        # Import scheduler from main module
        from main import scheduler

        if not scheduler:
            return {
                "status": "not_running",
                "message": "Scheduler is not initialized",
                "jobs": [],
                "timestamp": datetime.now().isoformat(),
            }

        # Get job information
        jobs = []
        for job in scheduler.get_jobs():
            next_run = job.next_run_time.isoformat() if job.next_run_time else None

            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": next_run,
                    "trigger": str(job.trigger),
                    "max_instances": job.max_instances,
                }
            )

        return {
            "status": "running" if scheduler.running else "stopped",
            "jobs": jobs,
            "job_count": len(jobs),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching scheduler status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error fetching scheduler status: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/return-to-ai")
async def return_conversation_to_ai(
    conversation_id: str,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_ops: SupabaseOperations = Depends(get_supabase_ops),
):
    """
    Return a conversation from human control back to AI automation.

    This endpoint allows human agents to re-enable AI automation
    for a conversation that was previously escalated.

    Args:
        conversation_id: Chatwoot conversation ID

    Returns:
        Success message
    """
    try:
        logger.info(f"Returning conversation {conversation_id} to AI control")

        state_key = f"session:{conversation_id}"
        state_data = None

        try:
            await redis_client.ensure_initialized()
            state_data = await redis_client.get_value(state_key, deserialize=True)
        except Exception as redis_error:
            logger.warning(
                "Redis unavailable during return-to-ai",
                extra={"conversation_id": conversation_id, "error": str(redis_error)},
            )

        if state_data:
            if isinstance(state_data, str):
                try:
                    state_data = json.loads(state_data)
                except Exception:
                    state_data = None

            if isinstance(state_data, dict):
                state_data["automation_paused"] = False
                state_data["human_takeover_reason"] = None
                try:
                    await redis_client.set_value(state_key, state_data, ttl=86400)
                except Exception as cache_error:
                    logger.warning(
                        "Failed to persist session state to Redis",
                        extra={
                            "conversation_id": conversation_id,
                            "error": str(cache_error),
                        },
                    )

        updated_at = datetime.now().isoformat()

        try:
            await supabase_ops.aupdate(
                "sessions",
                {
                    "automation_paused": False,
                    "human_takeover_reason": None,
                    "updated_at": updated_at,
                },
                {"conversation_id": conversation_id},
            )
        except CircuitBreakerError as cb_err:
            logger.error(
                "Supabase circuit breaker open while returning conversation to AI",
                extra={"conversation_id": conversation_id, "error": str(cb_err)},
            )
            raise HTTPException(
                status_code=503,
                detail="Supabase temporarily unavailable; tente novamente em instantes.",
            )
        except Exception as update_error:
            logger.error(
                f"Error updating conversation {conversation_id} in Supabase: {update_error}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="Error updating Supabase session for conversation.",
            )

        chatwoot_notified = True

        try:
            conv_id_int = int(conversation_id)
            await asyncio.to_thread(
                chatwoot_breaker.call,
                chatwoot_client.send_message,
                conv_id_int,
                "[OK] Automacao reativada. A IA voltara a responder mensagens nesta conversa.",
                "outgoing",
                True,
            )
        except ValueError:
            logger.error(
                "Invalid conversation_id for Chatwoot notification",
                extra={"conversation_id": conversation_id},
            )
            chatwoot_notified = False
        except CircuitBreakerError as cb_err:
            logger.warning(
                "Chatwoot circuit breaker open; skipping notification",
                extra={"conversation_id": conversation_id, "error": str(cb_err)},
            )
            chatwoot_notified = False
        except Exception as notify_error:
            logger.error(
                f"Failed to notify Chatwoot for conversation {conversation_id}: {notify_error}",
                exc_info=True,
            )
            chatwoot_notified = False

        logger.info(f"Conversation {conversation_id} returned to AI control")

        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "Conversation returned to AI automation",
            "chatwoot_notified": chatwoot_notified,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error returning conversation to AI: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error returning conversation to AI: {str(e)}"
        )


@router.post("/handoff-to-finance/{conversation_id}")
async def handoff_to_finance(
    conversation_id: str,
    request: Request,
    payload: Optional[dict] = None,
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_ops: SupabaseOperations = Depends(get_supabase_ops),
):
    """
    Encaminha conversa para o setor Financeiro (outra Inbox/número WhatsApp).
    
    Este endpoint pode ser chamado:
    - Via macro do Chatwoot (webhook simples)
    - Via API direta com autenticação
    
    Este endpoint:
    1. Pausa a automação na conversa atual
    2. Adiciona label "financeiro" para rastreabilidade
    3. Envia mensagem ao cliente informando sobre o encaminhamento
    4. Cria nota privada para histórico
    5. [Opcional] Cria conversa na Inbox do Financeiro se configurada
    6. Marca conversa atual como resolvida
    
    Args:
        conversation_id: Chatwoot conversation ID
        request: FastAPI Request object
        payload: Optional payload data
    
    Returns:
        Success message com detalhes do handoff
    """
    try:
        # Log da origem da requisição para auditoria
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Finance handoff request from {client_host} for conversation {conversation_id}"
        )
        logger.info(f"Starting finance handoff for conversation {conversation_id}")
        
        # Verificar se configuração do Financeiro existe
        finance_inbox_id = settings.chatwoot_finance_inbox_id
        finance_phone = settings.chatwoot_finance_phone
        
        if not finance_inbox_id:
            logger.warning("Finance inbox not configured, performing basic handoff only")
        
        # 1. Pausar automação na conversa atual
        state_key = f"session:{conversation_id}"
        
        try:
            await redis_client.ensure_initialized()
            state_data = await redis_client.get_value(state_key, deserialize=True)
            
            if state_data:
                if isinstance(state_data, str):
                    try:
                        state_data = json.loads(state_data)
                    except Exception:
                        state_data = {}
                
                if isinstance(state_data, dict):
                    state_data["automation_paused"] = True
                    state_data["human_takeover_reason"] = "finance_handoff"
                    await redis_client.set_value(state_key, state_data, ttl=86400)
        except Exception as redis_error:
            logger.warning(
                "Redis unavailable during finance handoff",
                extra={"conversation_id": conversation_id, "error": str(redis_error)}
            )
        
        # Atualizar Supabase
        updated_at = datetime.now().isoformat()
        try:
            await supabase_ops.aupdate(
                "sessions",
                {
                    "automation_paused": True,
                    "human_takeover_reason": "finance_handoff",
                    "updated_at": updated_at,
                },
                {"conversation_id": conversation_id},
            )
        except Exception as db_error:
            logger.error(
                f"Error updating session in Supabase: {db_error}",
                exc_info=True
            )
        
        # 2. Adicionar label "financeiro"
        try:
            conv_id_int = int(conversation_id)
            await asyncio.to_thread(
                chatwoot_breaker.call,
                chatwoot_client.add_labels,
                conv_id_int,
                ["financeiro"]
            )
        except Exception as label_error:
            logger.warning(f"Failed to add finance label: {label_error}")
        
        # 3. Enviar mensagem ao cliente
        finance_message = (
            "Obrigado pelo contato! 💙\n\n"
            "Vou encaminhar sua solicitação para nosso setor Financeiro, "
            "que possui expertise para melhor atendê-lo(a).\n\n"
        )
        
        if finance_phone:
            finance_message += (
                f"Você receberá contato pelo número: {finance_phone}\n\n"
                "Aguarde, em breve nossa equipe entrará em contato! ✨"
            )
        else:
            finance_message += (
                "Nossa equipe financeira entrará em contato em breve! ✨"
            )
        
        try:
            await asyncio.to_thread(
                chatwoot_breaker.call,
                chatwoot_client.send_message,
                conv_id_int,
                finance_message,
                "outgoing",
                False
            )
        except Exception as msg_error:
            logger.error(f"Failed to send finance handoff message: {msg_error}")
        
        # 4. Criar nota privada para histórico
        private_note = (
            f"🏦 **Encaminhado para Financeiro**\n\n"
            f"- Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"- Motivo: Solicitação financeira\n"
            f"- Automação: Pausada\n"
        )
        
        if finance_inbox_id:
            private_note += f"- Inbox Financeiro: ID {finance_inbox_id}\n"
        
        try:
            await asyncio.to_thread(
                chatwoot_breaker.call,
                chatwoot_client.send_message,
                conv_id_int,
                private_note,
                "outgoing",
                True  # Private note
            )
        except Exception as note_error:
            logger.warning(f"Failed to create private note: {note_error}")
        
        # 5. [Opcional] Criar conversa na Inbox do Financeiro
        finance_conversation_id = None
        if finance_inbox_id:
            try:
                # Buscar informações do contato da conversa atual
                conv_data = await asyncio.to_thread(
                    chatwoot_breaker.call,
                    chatwoot_client.get_conversation,
                    conv_id_int
                )
                
                if conv_data and conv_data.get("meta"):
                    contact = conv_data["meta"].get("sender")
                    if contact:
                        contact_id = contact.get("id")
                        phone = contact.get("phone_number", "")
                        
                        # Criar conversa na Inbox do Financeiro
                        new_conv = await asyncio.to_thread(
                            chatwoot_breaker.call,
                            chatwoot_client.create_conversation,
                            finance_inbox_id,
                            contact_id,
                            phone
                        )
                        
                        if new_conv:
                            finance_conversation_id = new_conv.get("id")
                            logger.info(
                                f"Created finance conversation: {finance_conversation_id}"
                            )
                            
                            # Enviar mensagem inicial na conversa do Financeiro
                            initial_message = (
                                f"📋 **Cliente encaminhado da conversa #{conversation_id}**\n\n"
                                f"Cliente possui solicitação financeira.\n"
                                f"Histórico disponível na conversa original."
                            )
                            
                            await asyncio.to_thread(
                                chatwoot_breaker.call,
                                chatwoot_client.send_message,
                                finance_conversation_id,
                                initial_message,
                                "outgoing",
                                True  # Private note
                            )
            except Exception as create_error:
                logger.warning(
                    f"Failed to create finance conversation: {create_error}",
                    exc_info=True
                )
        
        # 6. Marcar conversa atual como resolvida
        try:
            await asyncio.to_thread(
                chatwoot_breaker.call,
                chatwoot_client.toggle_status,
                conv_id_int,
                "resolved"
            )
        except Exception as status_error:
            logger.warning(f"Failed to resolve conversation: {status_error}")
        
        logger.info(
            f"Finance handoff completed for conversation {conversation_id}"
        )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "finance_conversation_id": finance_conversation_id,
            "message": "Conversation handed off to Finance team",
            "automation_paused": True,
            "timestamp": datetime.now().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error during finance handoff for conversation {conversation_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error during finance handoff: {str(e)}"
        )


