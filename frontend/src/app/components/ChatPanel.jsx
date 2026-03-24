import { useState, useRef, useCallback, useEffect } from 'react';
import {
    chatWithAssistant,
    downloadPlanDocument,
    generatePlan,
    generatePlanFromUpload,
    generateResponseFromUpload,
    getPlan,
    getPlanDocuments,
    regeneratePlanDocument,
    uploadDocument,
    getUpload,
    parseModel,
    parseInfraModel,
    saveProjectConversation,
    updateProjectConversation,
} from '../api.js';
import ContractorCards from './ContractorCards.jsx';
import { parseChatCommand } from '../lib/chatCommands.js';
import { formatParcelContext, formatMultiParcelContext } from '../lib/parcelState.js';
import { extractCentroid } from '../lib/geoUtils.js';
import {
    getConversations,
    getConversation,
    saveConversation,
    deleteConversation,
    createConversation,
    WELCOME_MESSAGE,
} from '../lib/chatHistory.js';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ChatContextHeader from './ChatContextHeader.jsx';
import useResizable from '../hooks/useResizable.js';

const POLL_INTERVAL_MS = 3000;

/** Convert basic markdown (bold, italic, line breaks) to HTML for chat messages. */
function inlineMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br/>');
}

function sleep(ms, signal) {
    if (signal?.aborted) {
        throw new DOMException('Request aborted', 'AbortError');
    }

    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            signal?.removeEventListener('abort', onAbort);
            resolve();
        }, ms);

        function onAbort() {
            clearTimeout(timer);
            reject(new DOMException('Request aborted', 'AbortError'));
        }

        signal?.addEventListener('abort', onAbort, { once: true });
    });
}

function isAbortError(error) {
    return error?.name === 'AbortError';
}

function planStartErrorMessage(error, filename = null) {
    if (error?.status === 401 || error?.status === 403) {
        return filename
            ? `Please sign in before generating a plan from ${filename}.`
            : 'Please sign in before generating a plan.';
    }
    return filename
        ? `Failed to start plan generation from ${filename}: ${error.message}`
        : `Failed to start generation: ${error.message}`;
}

export default function ChatPanel({ parcelContext, onPlanComplete, onToggleExpand, modelParams, onModelUpdate, analyzedUploads, activePlanId, selectedParcels, isComparisonMode, activeProjectId, activeProjectName, embedded = false }) {
    const { isResizing: isChatResizing, handleProps: chatResizeProps } = useResizable({
        defaultSize: 280,
        minSize: 150,
        maxSize: 600,
        axis: 'vertical',
        reverse: true,
        cssVar: '--chat-height',
    });

    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            text: "Hello! I'm your development due-diligence assistant. Search for a property above or ask me anything about zoning, policies, or development potential.",
        },
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(null);
    const [planProgress, setPlanProgress] = useState(null);
    const [latestAnalyzedUpload, setLatestAnalyzedUpload] = useState(null);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [showHistory, setShowHistory] = useState(false);

    const conversationHistoryRef = useRef([]);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const planPollControllersRef = useRef(new Map());
    const uploadPollControllerRef = useRef(null);
    const projectConvIdRef = useRef(null);

    const parcelContextStr = isComparisonMode
        ? formatMultiParcelContext(selectedParcels, parcelContext?.id)
        : formatParcelContext(parcelContext);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => {
        onToggleExpand?.(isExpanded);
    }, [isExpanded, onToggleExpand]);

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping, scrollToBottom]);

    // Initialize conversation on mount
    useEffect(() => {
        const conv = createConversation();
        setCurrentConversationId(conv.id);
        setMessages(conv.messages);
    }, []);

    // Auto-save messages (debounced) — localStorage + project backend
    useEffect(() => {
        if (!currentConversationId) return;
        // Only save if we have more than the welcome message
        if (messages.length <= 1) return;
        const timer = setTimeout(() => {
            saveConversation(currentConversationId, messages);
            // Also persist to project backend if a project is active
            if (activeProjectId) {
                const firstUserMsg = messages.find((m) => m.role === 'user');
                const title = firstUserMsg?.text?.slice(0, 80) || 'Chat';
                const payload = messages.map((m) => ({ role: m.role, text: m.text, timestamp: m.timestamp || new Date().toISOString() }));
                if (projectConvIdRef.current) {
                    updateProjectConversation(activeProjectId, projectConvIdRef.current, { messages: payload }).catch(() => {});
                } else {
                    saveProjectConversation(activeProjectId, { title, messages: payload })
                        .then((conv) => { projectConvIdRef.current = conv.id; })
                        .catch(() => {});
                }
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [messages, currentConversationId, activeProjectId]);

    const handleNewChat = useCallback(() => {
        // Save current conversation if it has user messages
        if (currentConversationId && messages.length > 1) {
            saveConversation(currentConversationId, messages);
        }
        const conv = createConversation();
        setCurrentConversationId(conv.id);
        setMessages(conv.messages);
        conversationHistoryRef.current = [];
        projectConvIdRef.current = null;
        setPlanProgress(null);
        setShowHistory(false);
    }, [currentConversationId, messages]);

    const handleLoadConversation = useCallback((id) => {
        // Save current first
        if (currentConversationId && messages.length > 1) {
            saveConversation(currentConversationId, messages);
        }
        const conv = getConversation(id);
        if (conv) {
            setCurrentConversationId(conv.id);
            setMessages(conv.messages);
            // Rebuild conversation history for AI context
            conversationHistoryRef.current = conv.messages
                .filter((m) => m.role === 'user' || m.role === 'assistant')
                .map(({ role, text }) => ({ role, text }));
            setPlanProgress(null);
        }
        setShowHistory(false);
    }, [currentConversationId, messages]);

    const handleDeleteConversation = useCallback((id) => {
        deleteConversation(id);
        // If deleting the active conversation, start a new one
        if (id === currentConversationId) {
            const conv = createConversation();
            setCurrentConversationId(conv.id);
            setMessages(conv.messages);
            conversationHistoryRef.current = [];
            setPlanProgress(null);
        }
    }, [currentConversationId]);

    const handleToggle = useCallback(() => {
        setIsExpanded((prev) => !prev);
    }, []);

    const cancelPlanPoll = useCallback((key) => {
        if (key != null) {
            const ctrl = planPollControllersRef.current.get(key);
            if (ctrl) { ctrl.abort(); planPollControllersRef.current.delete(key); }
        } else {
            planPollControllersRef.current.forEach((ctrl) => ctrl.abort());
            planPollControllersRef.current.clear();
        }
    }, []);

    const cancelUploadPoll = useCallback(() => {
        uploadPollControllerRef.current?.abort();
        uploadPollControllerRef.current = null;
    }, []);

    useEffect(() => () => {
        cancelPlanPoll(); // abort all
        cancelUploadPoll();
    }, [cancelPlanPoll, cancelUploadPoll]);

    const STEP_LABELS = {
        query_parsing: 'Parsing query',
        parcel_lookup: 'Looking up parcel',
        policy_resolution: 'Resolving policies & zoning',
        massing_generation: 'Generating massing',
        layout_optimization: 'Optimizing layout',
        financial_analysis: 'Running financial analysis',
        entitlement_check: 'Checking compliance',
        precedent_search: 'Searching precedents',
        document_generation: 'Generating documents',
    };
    const STEP_ORDER = Object.keys(STEP_LABELS);

    const pollPlan = useCallback(async (planId, pollKey) => {
        const key = pollKey ?? planId;
        cancelPlanPoll(key);
        const controller = new AbortController();
        const { signal } = controller;
        planPollControllersRef.current.set(key, controller);
        const maxAttempts = 120;

        try {
            let consecutiveErrors = 0;
            for (let i = 0; i < maxAttempts; i++) {
                await sleep(POLL_INTERVAL_MS, signal);

                let plan;
                try {
                    plan = await getPlan(planId, { signal });
                    consecutiveErrors = 0;
                } catch (pollErr) {
                    if (isAbortError(pollErr)) return;
                    consecutiveErrors++;
                    console.warn(`Plan poll attempt ${i + 1} failed (${consecutiveErrors} consecutive):`, pollErr.message);
                    if (consecutiveErrors >= 5) {
                        setMessages((prev) => [...prev, {
                            role: 'assistant',
                            text: `Lost connection to the server while checking plan progress. The plan may still be generating — try refreshing the page.`,
                        }]);
                        return;
                    }
                    continue;
                }
                if (signal.aborted) return;

                // Update progress
                if (plan.status === 'running_pipeline' && plan.current_step) {
                    const completedCount = plan.pipeline_progress
                        ? Object.keys(plan.pipeline_progress).filter((k) => k !== '_doc_progress' && plan.pipeline_progress[k] === 'completed').length
                        : 0;
                    const pct = Math.round((completedCount / STEP_ORDER.length) * 100);
                    const docProgress = plan.pipeline_progress?._doc_progress;
                    let stepLabel = STEP_LABELS[plan.current_step] || plan.current_step;
                    if (plan.current_step === 'document_generation' && docProgress) {
                        stepLabel = `Generating ${docProgress.current_doc_title} (${docProgress.completed_docs + 1}/${docProgress.total_docs})`;
                    }
                    setPlanProgress({
                        step: stepLabel,
                        pct,
                        completedCount,
                        totalSteps: STEP_ORDER.length,
                    });
                }

                if (plan.status === 'completed' || plan.status === 'done') {
                    setPlanProgress(null);
                    const docs = await getPlanDocuments(planId, { signal }).catch(() => []);
                    if (signal.aborted) return;

                    setMessages((prev) => [...prev, {
                        role: 'assistant',
                        text: 'Plan generation complete!',
                        documents: docs,
                        planId,
                    }]);
                    if (onPlanComplete && plan.summary?.massing) {
                        onPlanComplete(plan.summary.massing, planId);
                    }
                    return;
                }
                if (plan.status === 'failed' || plan.status === 'error') {
                    setPlanProgress(null);
                    setMessages((prev) => [...prev, {
                        role: 'assistant',
                        text: `Plan generation failed. ${plan.error_message || 'Please try again.'}`,
                    }]);
                    return;
                }
                if (plan.status === 'needs_clarification') {
                    setPlanProgress(null);
                    const questions = plan.clarification_questions || [];
                    setMessages((prev) => [...prev, {
                        role: 'assistant',
                        text: `I need some clarification before proceeding:\n\n${questions.map((q, i) => `${i + 1}. ${q}`).join('\n')}`,
                    }]);
                    return;
                }
            }
        } catch (error) {
            if (!isAbortError(error)) {
                console.error('Plan polling error:', error);
            }
            return;
        } finally {
            setPlanProgress(null);
            if (planPollControllersRef.current.get(key) === controller) {
                planPollControllersRef.current.delete(key);
            }
        }

        if (!signal.aborted) {
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: 'Plan generation is still in progress. Check back shortly.',
            }]);
        }
    }, [cancelPlanPoll, onPlanComplete]);

    const handleGenerateAction = useCallback(async (action, msgIdx) => {
        // Disable the button on the message that proposed it
        setMessages((prev) => prev.map((m, i) =>
            i === msgIdx ? { ...m, actionFired: true } : m
        ));
        setMessages((prev) => [...prev, {
            role: 'assistant',
            text: `Starting: ${action.label}...`,
            isGenerating: true,
        }]);

        const docTypes = action.doc_types;
        const isSmallSubset = Array.isArray(docTypes) && docTypes.length <= 3;

        // If comparing multiple parcels, run pipeline with parcel_ids for downloadable comparison report
        if (isComparisonMode && selectedParcels?.length >= 2) {
            const parcelIds = selectedParcels.map(p => p.id).filter(Boolean);
            try {
                const result = await generatePlan(action.query, docTypes, activeProjectId, parcelIds);
                setMessages((prev) => prev.map(m => m.isGenerating ? { ...m, isGenerating: false } : m));
                pollPlan(result.job_id);
            } catch (err) {
                setMessages((prev) => prev.map(m => m.isGenerating ? { ...m, isGenerating: false } : m));
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Failed to generate comparison report: ${err.message}`,
                }]);
            }
            return;
        }

        try {
            // Smart routing: if an active plan exists and we're generating ≤3 docs,
            // regenerate from existing plan data (no pipeline re-run)
            if (activePlanId && isSmallSubset) {
                const results = [];
                for (const dt of docTypes) {
                    const doc = await regeneratePlanDocument(activePlanId, dt, {});
                    results.push(doc);
                }
                const docList = results.map((d) => `- ${d.title || d.doc_type}`).join('\n');
                setMessages((prev) => prev.map(m => m.isGenerating ? { ...m, isGenerating: false } : m));
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Documents generated from existing plan:\n\n${docList}`,
                }]);
            } else {
                // No existing plan or large batch — run full pipeline
                const result = await generatePlan(action.query, docTypes, activeProjectId);
                setMessages((prev) => prev.map(m => m.isGenerating ? { ...m, isGenerating: false } : m));
                pollPlan(result.job_id);
            }
        } catch (err) {
            setMessages((prev) => prev.map(m => m.isGenerating ? { ...m, isGenerating: false } : m));
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: planStartErrorMessage(err),
            }]);
        }
    }, [pollPlan, activePlanId, activeProjectId, isComparisonMode, selectedParcels]);

    const handleGenerateReport = useCallback(async () => {
        if (isComparisonMode && selectedParcels?.length >= 2) {
            // Multi-parcel comparison report: generate in parallel with per-parcel try/catch
            const parcels = selectedParcels.filter(p => p.address || p.zoneCode);
            if (parcels.length === 0) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: 'Please search for properties first so I know which parcels to generate reports for.',
                }]);
                return;
            }
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Starting comparison report for ${parcels.length} parcels...`,
            }]);
            let completed = 0;
            const results = await Promise.all(parcels.map(async (p) => {
                const addr = p.address || p.fullAddress || 'Unknown';
                const zone = p.zoneCode || p.zone_code || p.zoning;
                const lotArea = p.lotArea;
                const reportQuery = [
                    `I want to build a mixed-use development at ${addr}, Toronto, Ontario.`,
                    zone ? `The site is zoned ${zone}.` : '',
                    lotArea ? `Lot area is ${lotArea} m\u00B2.` : '',
                    'Generate the full submission package.',
                ].filter(Boolean).join(' ');
                try {
                    const result = await generatePlan(reportQuery, null, activeProjectId);
                    completed++;
                    setPlanProgress({
                        step: `Generating reports: ${completed}/${parcels.length} started`,
                        pct: Math.round((completed / parcels.length) * 100),
                        completedCount: completed,
                        totalSteps: parcels.length,
                    });
                    pollPlan(result.job_id, `comparison-${p.id}`);
                    return { parcel: addr, jobId: result.job_id, error: null };
                } catch (err) {
                    completed++;
                    return { parcel: addr, jobId: null, error: err.message };
                }
            }));
            setPlanProgress(null);
            const failures = results.filter(r => r.error);
            if (failures.length > 0) {
                const failList = failures.map(f => `- ${f.parcel}: ${f.error}`).join('\n');
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Some reports failed to start:\n\n${failList}`,
                }]);
            }
            const successes = results.filter(r => r.jobId);
            if (successes.length > 0) {
                const successList = successes.map(s => `- ${s.parcel}`).join('\n');
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Report generation started for:\n\n${successList}\n\nI'll update you as each completes...`,
                }]);
            }
            return;
        }

        // Single-parcel report
        const addr = parcelContext?.address || parcelContext?.fullAddress || parcelContext?.addr;
        const zone = parcelContext?.zoneCode || parcelContext?.zone_code || parcelContext?.zoning;
        if (!parcelContext || (!addr && !zone)) {
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: 'Please search for a property first so I know which parcel to generate the report for.',
            }]);
            return;
        }
        const lotArea = parcelContext?.lotArea;
        const reportQuery = [
            `I want to build a mixed-use development at ${addr}, Toronto, Ontario.`,
            zone ? `The site is zoned ${zone}.` : '',
            lotArea ? `Lot area is ${lotArea} m\u00B2.` : '',
            'Generate the full submission package.',
        ].filter(Boolean).join(' ');
        try {
            const result = await generatePlan(reportQuery, null, activeProjectId);
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Report generation started for <strong>${addr}</strong>. I'll update you as each step completes...`,
            }]);
            pollPlan(result.job_id);
        } catch (err) {
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: planStartErrorMessage(err),
            }]);
        }
    }, [isComparisonMode, selectedParcels, parcelContext, pollPlan, activeProjectId]);

    const sendMessage = useCallback(async () => {
        const text = inputValue.trim();
        if (!text) return;

        const nextHistory = [...conversationHistoryRef.current, { role: 'user', text }];
        setInputValue('');
        setMessages((prev) => [...prev, { role: 'user', text }]);
        conversationHistoryRef.current = nextHistory;
        setIsTyping(true);

        // Keep upload-specific commands as direct shortcuts
        const command = parseChatCommand(text);

        if (command.type === 'infra_model') {
            try {
                const params = await parseInfraModel(text, modelParams, 'pipeline');
                onModelUpdate?.(params);
                let infraMsg = `Pipeline design updated: ${params.diameter_mm || 0}mm ${params.material || ''} ${params.infra_type || ''} pipe, ${params.length_m || 0}m length.`;
                if (params.warnings?.length) {
                    infraMsg += '\n-- ' + params.warnings.join('\n-- ');
                }
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: infraMsg,
                }]);
            } catch (err) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Couldn't parse infrastructure description: ${err.message}`,
                }]);
            } finally {
                setIsTyping(false);
            }
            return;
        }

        if (command.type === 'model') {
            try {
                const zoneCode = parcelContext?.zoneCode || parcelContext?.zone_code || parcelContext?.zoning || null;
                const lotAreaM2 = parcelContext?.lotArea ?? parcelContext?.lot_area_m2 ?? null;
                const params = await parseModel(text, modelParams, zoneCode, lotAreaM2);
                onModelUpdate?.(params);
                let modelMsg = `Building updated: ${params.storeys} storeys, ${params.height_m}m tall (${(params.typology || '').replace(/_/g, ' ')}).`;
                if (params.warnings?.length) {
                    modelMsg += '\n-- ' + params.warnings.join('\n-- ');
                }
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: modelMsg,
                }]);
            } catch (err) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Couldn't parse building description: ${err.message}`,
                }]);
            } finally {
                setIsTyping(false);
            }
            return;
        }

        if (command.type === 'plan_from_upload') {
            if (!latestAnalyzedUpload?.id) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: 'There is no analyzed upload ready yet. Upload a document and wait for analysis to finish before generating a plan from it.',
                }]);
                setIsTyping(false);
                return;
            }
            try {
                const result = await generatePlanFromUpload(latestAnalyzedUpload.id);
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Plan generation started from ${latestAnalyzedUpload.filename}. I'll let you know when it's ready...`,
                }]);
                setIsTyping(false);
                pollPlan(result.job_id);
                return;
            } catch (err) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: planStartErrorMessage(err, latestAnalyzedUpload.filename),
                }]);
                setIsTyping(false);
                return;
            }
        }

        if (command.type === 'response_from_upload') {
            if (!latestAnalyzedUpload?.id) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: 'There is no analyzed upload ready yet. Upload a document and wait for analysis to finish before generating a response from it.',
                }]);
                setIsTyping(false);
                return;
            }
            try {
                const result = await generateResponseFromUpload(latestAnalyzedUpload.id);
                const responseLabel = (result.response_type || 'response').replace(/_/g, ' ');
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Generated ${responseLabel} from ${latestAnalyzedUpload.filename}:\n\n${result.content}`,
                }]);
            } catch (err) {
                setMessages((prev) => [...prev, {
                    role: 'assistant',
                    text: `Failed to generate a response from ${latestAnalyzedUpload.filename}: ${err.message}`,
                }]);
            } finally {
                setIsTyping(false);
            }
            return;
        }

        if (command.type === 'generate_report') {
            setIsTyping(false);
            handleGenerateReport();
            return;
        }

        // All other messages go to the AI — it decides whether to answer, propose generation, or update the model
        try {
            const zoneCode = parcelContext?.zoneCode || parcelContext?.zone_code || parcelContext?.zoning || null;
            const uploadContext = (analyzedUploads || []).map((u) => ({
                filename: u.filename,
                extracted_data: u.extractedData || null,
            }));
            // Extract lat/lng from parcel geometry for infrastructure queries
            const centroid = extractCentroid(parcelContext?.geom);
            const parcelLng = centroid?.[0] ?? null;
            const parcelLat = centroid?.[1] ?? null;

            const zoneCodes = isComparisonMode
                ? [...new Set(selectedParcels.filter(p => p.zoneCode).map(p => p.zoneCode))]
                : null;

            const { message, proposedAction, modelUpdate, contractors } = await chatWithAssistant({
                messages: nextHistory.slice(-20),
                parcelContext: parcelContextStr,
                parcelId: parcelContext?.id || null,
                lat: parcelLat,
                lng: parcelLng,
                modelParams: modelParams || null,
                zoneCode,
                zoneCodes,
                uploadContext: uploadContext.length ? uploadContext : null,
            });

            // If the AI decided to update the 3D model, apply it
            if (modelUpdate) {
                onModelUpdate?.(modelUpdate);
            }

            let displayMsg = message;
            if (modelUpdate?.warnings?.length) {
                displayMsg += '\n⚠ ' + modelUpdate.warnings.join('\n⚠ ');
            }

            const assistantMessage = {
                role: 'assistant',
                text: displayMsg,
                action: proposedAction || null,
                actionFired: false,
                contractors: contractors || [],
            };
            setMessages((prev) => [...prev, assistantMessage]);
            conversationHistoryRef.current = [...nextHistory, { role: 'assistant', text: message }];
        } catch (err) {
            console.error('Assistant chat error:', err);
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Sorry, I couldn't get a response right now. ${err.message}`,
            }]);
        } finally {
            setIsTyping(false);
        }
    }, [inputValue, latestAnalyzedUpload, modelParams, onModelUpdate, parcelContext, parcelContextStr, pollPlan, handleGenerateReport, isComparisonMode, selectedParcels]);

    const pollUpload = useCallback(async (uploadId, filename) => {
        cancelUploadPoll();
        const controller = new AbortController();
        const { signal } = controller;
        uploadPollControllerRef.current = controller;
        const maxAttempts = 40;

        try {
            for (let i = 0; i < maxAttempts; i++) {
                await sleep(POLL_INTERVAL_MS, signal);
                const upload = await getUpload(uploadId, { signal });
                if (signal.aborted) return;

                if (upload.status === 'analyzed') {
                    setUploadProgress(null);
                    const ed = upload.extracted_data || {};

                    // Pipeline DXF path
                    if (ed.pipeline_network) {
                        const net = ed.pipeline_network;
                        const s = net.summary || {};
                        const parts = [
                            `Pipeline DXF analyzed: ${filename}`,
                            `Network: ${s.pipe_count ?? 0} pipe segments · ${s.total_length_m ?? 0}m total length`,
                        ];
                        if (s.manhole_count) parts.push(`Manholes: ${s.manhole_count}`);
                        if (s.valve_count) parts.push(`Valves: ${s.valve_count}`);
                        if (s.hydrant_count) parts.push(`Hydrants: ${s.hydrant_count}`);
                        parts.push('\nThe 3D pipeline viewer has opened. Click any pipe or manhole to edit its properties.');
                        setMessages((prev) => [...prev, { role: 'assistant', text: parts.join('\n') }]);
                        setLatestAnalyzedUpload({ id: uploadId, filename });
                        return;
                    }

                    // Standard document path
                    const parts = [`Document analyzed: ${filename}`];
                    if (upload.doc_category) parts.push(`Category: ${upload.doc_category.replace(/_/g, ' ')}`);
                    if (upload.page_count) parts.push(`Pages: ${upload.page_count}`);
                    if (ed && !ed.error && !ed.note) {
                        const b = ed.building || {};
                        const items = [];
                        if (b.storeys) items.push(`${b.storeys} storeys`);
                        if (b.unit_count) items.push(`${b.unit_count} units`);
                        if (b.height_m) items.push(`${b.height_m}m height`);
                        if (items.length) parts.push(`Extracted: ${items.join(', ')}`);
                    }
                    if (upload.compliance_findings?.issues?.length) {
                        parts.push(`Compliance issues found: ${upload.compliance_findings.issues.length}`);
                    }
                    parts.push(`\nSay "generate plan from upload" or "generate response from upload" to proceed.`);
                    setMessages((prev) => [...prev, { role: 'assistant', text: parts.join('\n') }]);
                    setLatestAnalyzedUpload({ id: uploadId, filename });
                    return;
                }
                if (upload.status === 'failed') {
                    setUploadProgress(null);
                    setMessages((prev) => [...prev, {
                        role: 'assistant',
                        text: `Document analysis failed for ${filename}. ${upload.error_message || 'Please try again.'}`,
                    }]);
                    return;
                }
                setUploadProgress({ filename, status: upload.status });
            }
        } catch (error) {
            if (!isAbortError(error)) {
                console.error('Upload polling error:', error);
            }
            return;
        } finally {
            if (uploadPollControllerRef.current === controller) {
                uploadPollControllerRef.current = null;
            }
        }

        if (!signal.aborted) {
            setUploadProgress(null);
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Document analysis is still in progress for ${filename}. Check back shortly.`,
            }]);
        }
    }, [cancelUploadPoll]);

    const handleFileUpload = useCallback(async (file) => {
        if (!file) return;
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            setMessages((prev) => [...prev, { role: 'assistant', text: 'File exceeds 50 MB limit.' }]);
            return;
        }
        setMessages((prev) => [...prev, { role: 'user', text: `Uploading: ${file.name}` }]);
        setUploadProgress({ filename: file.name, status: 'uploading' });
        try {
            const result = await uploadDocument(file);
            setUploadProgress({ filename: file.name, status: 'processing' });
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Uploaded ${file.name} — analyzing document...`,
            }]);
            pollUpload(result.id, file.name);
        } catch (err) {
            setUploadProgress(null);
            setMessages((prev) => [...prev, {
                role: 'assistant',
                text: `Upload failed: ${err.message}`,
            }]);
        }
    }, [pollUpload]);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer?.files?.[0];
        if (file) handleFileUpload(file);
    }, [handleFileUpload]);

    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragOver(false);
    }, []);

    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }, [sendMessage]);

    const chatToolbar = (
        <div className="chat-toolbar" onClick={(e) => e.stopPropagation()} style={embedded ? { padding: '4px 8px', borderBottom: '1px solid var(--border)' } : undefined}>
            <button className="chat-toolbar-btn" title="New Chat" onClick={handleNewChat}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="15" height="15">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
            </button>
            <button className="chat-toolbar-btn" title="Chat History" onClick={() => setShowHistory((v) => !v)}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="15" height="15">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                </svg>
            </button>
        </div>
    );

    if (embedded) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                {chatToolbar}
                <ChatContextHeader
                    selectedParcels={selectedParcels}
                    primaryParcel={parcelContext}
                    analyzedUploads={analyzedUploads}
                    activePlanId={activePlanId}
                    isExpanded={true}
                    onGenerateReport={handleGenerateReport}
                />
                <div id="chat-body" onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave} style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                {isDragOver && (
                    <div className="chat-drop-overlay">
                        <div className="chat-drop-content">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="32" height="32">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="17 8 12 3 7 8" />
                                <line x1="12" y1="3" x2="12" y2="15" />
                            </svg>
                            <span>Drop file to upload</span>
                        </div>
                    </div>
                )}
                {showHistory && (
                    <div className="chat-history-panel">
                        <div className="chat-history-header">
                            <span>Chat History</span>
                            <button className="chat-history-close" onClick={() => setShowHistory(false)}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                        <div className="chat-history-list">
                            {getConversations().length === 0 ? (
                                <div className="chat-history-empty">No saved conversations yet</div>
                            ) : (
                                getConversations().map((conv) => (
                                    <div
                                        key={conv.id}
                                        className={`chat-history-item ${conv.id === currentConversationId ? 'active' : ''}`}
                                        onClick={() => handleLoadConversation(conv.id)}
                                    >
                                        <div className="chat-history-item-content">
                                            <div className="chat-history-title">{conv.title}</div>
                                            <div className="chat-history-date">
                                                {new Date(conv.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            </div>
                                        </div>
                                        <button
                                            className="chat-history-delete"
                                            title="Delete conversation"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteConversation(conv.id);
                                            }}
                                        >
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                                <line x1="18" y1="6" x2="6" y2="18" />
                                                <line x1="6" y1="6" x2="18" y2="18" />
                                            </svg>
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
                <div id="chat-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`chat-message ${msg.role}`}>
                            <div className="message-avatar">{msg.role === 'assistant' ? 'AI' : 'You'}</div>
                            <div className="message-content">
                                <div className="extract-markdown" style={{ margin: 0 }}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text || ''}</ReactMarkdown>
                                </div>
                                {msg.isGenerating && (
                                    <div className="upload-status" style={{ marginTop: 8 }}>
                                        <div className="upload-spinner"></div>
                                        <span>Generating report&hellip;</span>
                                    </div>
                                )}
                                {msg.documents?.length > 0 && (
                                    <div className="chat-doc-list">
                                        {msg.documents.map((doc) => (
                                            <div key={doc.id} className="chat-doc-item">
                                                <div className="chat-doc-icon">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="16" height="16">
                                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                                        <polyline points="14 2 14 8 20 8" />
                                                    </svg>
                                                </div>
                                                <span className="chat-doc-title">{doc.title || doc.doc_type}</span>
                                                <button
                                                    className="chat-doc-download"
                                                    title="Download as Markdown"
                                                    onClick={async () => {
                                                        try {
                                                            const res = await downloadPlanDocument(msg.planId, doc.id, 'markdown');
                                                            const blob = await res.blob();
                                                            const url = URL.createObjectURL(blob);
                                                            const a = document.createElement('a');
                                                            a.href = url;
                                                            a.download = `${(doc.title || doc.doc_type).replace(/\s+/g, '_')}.md`;
                                                            a.click();
                                                            URL.revokeObjectURL(url);
                                                        } catch (err) {
                                                            console.error('Download failed:', err);
                                                        }
                                                    }}
                                                >
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                        <polyline points="7 10 12 15 17 10" />
                                                        <line x1="12" y1="15" x2="12" y2="3" />
                                                    </svg>
                                                    .md
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {msg.contractors?.length > 0 && (
                                    <ContractorCards contractors={msg.contractors} />
                                )}
                                {msg.role === 'assistant' && msg.action && !msg.actionFired && (
                                    <button
                                        className="generate-action-btn"
                                        onClick={() => handleGenerateAction(msg.action, idx)}
                                    >
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                            <line x1="12" y1="18" x2="12" y2="12" />
                                            <line x1="9" y1="15" x2="15" y2="15" />
                                        </svg>
                                        {msg.action.label}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                    {planProgress && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="plan-progress">
                                    <div className="plan-progress-header">
                                        <div className="upload-spinner"></div>
                                        <span>{planProgress.step}... ({planProgress.completedCount}/{planProgress.totalSteps})</span>
                                    </div>
                                    <div className="plan-progress-bar">
                                        <div className="plan-progress-fill" style={{ width: `${planProgress.pct}%` }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    {uploadProgress && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="upload-status">
                                    <div className="upload-spinner"></div>
                                    <span>{uploadProgress.status === 'uploading' ? 'Uploading' : 'Analyzing'} {uploadProgress.filename}...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    {isTyping && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div id="chat-input-container">
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }}
                        accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv"
                        onChange={(e) => { handleFileUpload(e.target.files?.[0]); e.target.value = ''; }}
                    />
                    <button className="chat-upload-btn" aria-label="Upload file" title="Upload a document for AI analysis"
                        onClick={() => fileInputRef.current?.click()}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                        </svg>
                    </button>
                    <input
                        type="text"
                        id="chat-input"
                        placeholder="Ask about zoning, setbacks, variance requirements..."
                        autoComplete="off"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    <button id="chat-send" aria-label="Send message" onClick={sendMessage}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="22" y1="2" x2="11" y2="13" />
                            <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        );
    }

    return (
        <div id="chat-panel" className={`${isExpanded ? 'expanded' : ''} backdrop-blur-xl`} style={{ userSelect: isChatResizing ? 'none' : undefined }}>
            {isExpanded && <div {...chatResizeProps} style={{ ...chatResizeProps.style, top: -2 }} />}
            <div id="chat-toggle" role="button" tabIndex="0" aria-label="Toggle chat" onClick={handleToggle}>
                <div id="chat-toggle-left">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    <span>Ask the AI Agent</span>
                </div>
                {isExpanded && chatToolbar}
                <svg id="chat-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15" />
                </svg>
            </div>
            <ChatContextHeader
                selectedParcels={selectedParcels}
                primaryParcel={parcelContext}
                analyzedUploads={analyzedUploads}
                activePlanId={activePlanId}
                isExpanded={isExpanded}
                onGenerateReport={handleGenerateReport}
            />
            <div id="chat-body" onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave}>
                {isDragOver && (
                    <div className="chat-drop-overlay">
                        <div className="chat-drop-content">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="32" height="32">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="17 8 12 3 7 8" />
                                <line x1="12" y1="3" x2="12" y2="15" />
                            </svg>
                            <span>Drop file to upload</span>
                        </div>
                    </div>
                )}
                {showHistory && (
                    <div className="chat-history-panel">
                        <div className="chat-history-header">
                            <span>Chat History</span>
                            <button className="chat-history-close" onClick={() => setShowHistory(false)}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            </button>
                        </div>
                        <div className="chat-history-list">
                            {getConversations().length === 0 ? (
                                <div className="chat-history-empty">No saved conversations yet</div>
                            ) : (
                                getConversations().map((conv) => (
                                    <div
                                        key={conv.id}
                                        className={`chat-history-item ${conv.id === currentConversationId ? 'active' : ''}`}
                                        onClick={() => handleLoadConversation(conv.id)}
                                    >
                                        <div className="chat-history-item-content">
                                            <div className="chat-history-title">{conv.title}</div>
                                            <div className="chat-history-date">
                                                {new Date(conv.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            </div>
                                        </div>
                                        <button
                                            className="chat-history-delete"
                                            title="Delete conversation"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteConversation(conv.id);
                                            }}
                                        >
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                                <line x1="18" y1="6" x2="6" y2="18" />
                                                <line x1="6" y1="6" x2="18" y2="18" />
                                            </svg>
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
                <div id="chat-messages">
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`chat-message ${msg.role}`}>
                            <div className="message-avatar">{msg.role === 'assistant' ? 'AI' : 'You'}</div>
                            <div className="message-content">
                                <div className="extract-markdown" style={{ margin: 0 }}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text || ''}</ReactMarkdown>
                                </div>
                                {msg.isGenerating && (
                                    <div className="upload-status" style={{ marginTop: 8 }}>
                                        <div className="upload-spinner"></div>
                                        <span>Generating report&hellip;</span>
                                    </div>
                                )}
                                {msg.documents?.length > 0 && (
                                    <div className="chat-doc-list">
                                        {msg.documents.map((doc) => (
                                            <div key={doc.id} className="chat-doc-item">
                                                <div className="chat-doc-icon">
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="16" height="16">
                                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                                        <polyline points="14 2 14 8 20 8" />
                                                    </svg>
                                                </div>
                                                <span className="chat-doc-title">{doc.title || doc.doc_type}</span>
                                                <button
                                                    className="chat-doc-download"
                                                    title="Download as Markdown"
                                                    onClick={async () => {
                                                        try {
                                                            const res = await downloadPlanDocument(msg.planId, doc.id, 'markdown');
                                                            const blob = await res.blob();
                                                            const url = URL.createObjectURL(blob);
                                                            const a = document.createElement('a');
                                                            a.href = url;
                                                            a.download = `${(doc.title || doc.doc_type).replace(/\s+/g, '_')}.md`;
                                                            a.click();
                                                            URL.revokeObjectURL(url);
                                                        } catch (err) {
                                                            console.error('Download failed:', err);
                                                        }
                                                    }}
                                                >
                                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                                                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                                        <polyline points="7 10 12 15 17 10" />
                                                        <line x1="12" y1="15" x2="12" y2="3" />
                                                    </svg>
                                                    .md
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {msg.contractors?.length > 0 && (
                                    <ContractorCards contractors={msg.contractors} />
                                )}
                                {msg.role === 'assistant' && msg.action && !msg.actionFired && (
                                    <button
                                        className="generate-action-btn"
                                        onClick={() => handleGenerateAction(msg.action, idx)}
                                    >
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                            <line x1="12" y1="18" x2="12" y2="12" />
                                            <line x1="9" y1="15" x2="15" y2="15" />
                                        </svg>
                                        {msg.action.label}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                    {planProgress && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="plan-progress">
                                    <div className="plan-progress-header">
                                        <div className="upload-spinner"></div>
                                        <span>{planProgress.step}... ({planProgress.completedCount}/{planProgress.totalSteps})</span>
                                    </div>
                                    <div className="plan-progress-bar">
                                        <div className="plan-progress-fill" style={{ width: `${planProgress.pct}%` }} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    {uploadProgress && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="upload-status">
                                    <div className="upload-spinner"></div>
                                    <span>{uploadProgress.status === 'uploading' ? 'Uploading' : 'Analyzing'} {uploadProgress.filename}...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    {isTyping && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">AI</div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
                <div id="chat-input-container">
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }}
                        accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv"
                        onChange={(e) => { handleFileUpload(e.target.files?.[0]); e.target.value = ''; }}
                    />
                    <button className="chat-upload-btn" aria-label="Upload file" title="Upload a document for AI analysis"
                        onClick={() => fileInputRef.current?.click()}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                        </svg>
                    </button>
                    <input
                        type="text"
                        id="chat-input"
                        placeholder="Ask about zoning, setbacks, variance requirements..."
                        autoComplete="off"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    <button id="chat-send" aria-label="Send message" onClick={sendMessage}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="22" y1="2" x2="11" y2="13" />
                            <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
}
