import { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Loader2, Bot, User, CheckCircle2, ShieldAlert } from 'lucide-react';
import { Drawer } from '@/components/ui/Drawer';
import { Badge } from '@/components/ui/Badge';
import { aiApi } from '@/services/api/aiApi';
import type { AssistantToolDefinition } from '@/api/ai';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  toolInvoked?: string | null;
  tokensUsed?: number;
  latencyMs?: number;
  timestamp: string;
}

const DOMAIN_QUICK_PILLS = [
  { label: '🎓 Academic Risk', prompt: 'Which students are at high academic risk?', tool: 'get_academic_risk_summary' },
  { label: '📊 Attendance', prompt: 'What is the overall attendance percentage for the last 30 days?', tool: 'get_attendance_analytics' },
  { label: '💰 Fee Status', prompt: 'What is the fee collection and delinquency status?', tool: 'get_fee_delinquency_summary' },
  { label: '📝 Exam Performance', prompt: 'What is the pass rate and average score for term exams?', tool: 'get_exam_performance_summary' },
  { label: '📚 Homework Rate', prompt: 'What is the homework completion rate over the last 30 days?', tool: 'get_homework_completion_summary' },
  { label: '🗓️ Timetable Loads', prompt: 'How many periods are scheduled for today?', tool: 'get_timetable_schedule_summary' },
  { label: '👥 Staff Absences', prompt: 'How many staff members are on leave today?', tool: 'get_staff_leave_summary' },
];

interface AIAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AIAssistantDrawer = ({ isOpen, onClose }: AIAssistantDrawerProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your **AI Operational Assistant**. Ask me about Academic Risk, Attendance, Fees, Exams, Homework, Timetables, or Staff Absences.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [availableTools, setAvailableTools] = useState<AssistantToolDefinition[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      aiApi.listTools()
        .then((tools) => setAvailableTools(tools))
        .catch(() => setAvailableTools([]));
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (promptText?: string) => {
    const textToSend = (promptText || inputMessage).trim();
    if (!textToSend || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!promptText) setInputMessage('');
    setLoading(true);

    try {
      const response = await aiApi.chat({ message: textToSend });

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: 'assistant',
        text: response.reply,
        toolInvoked: response.tool_invoked,
        tokensUsed: response.tokens_used,
        latencyMs: response.latency_ms,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Execution failed';
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ **Assistant Error**: ${errorMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const isToolAvailable = (toolName: string) => {
    if (availableTools.length === 0) return true; // Default fallback before tools load
    return availableTools.some((t) => t.name === toolName);
  };

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="AI Operational Analytics Assistant"
      width="lg"
    >
      <div className="flex flex-col h-[calc(100vh-8rem)] text-ink dark:text-stone-100">
        {/* Available Tools Bar */}
        <div className="px-3 py-2 bg-paper-dim dark:bg-stone-900 border-b border-divider dark:border-stone-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Multi-Domain Function Engine</span>
          </div>
          <span className="font-mono text-[10px] text-ink-muted dark:text-stone-400">
            {availableTools.length} Tools Whitelisted
          </span>
        </div>

        {/* Domain Quick Action Pills */}
        <div className="p-3 border-b border-divider dark:border-stone-800 bg-paper dark:bg-stone-950">
          <p className="text-[11px] font-semibold text-ink-muted dark:text-stone-400 uppercase tracking-wider mb-2">
            Quick Operational Insights
          </p>
          <div className="flex flex-wrap gap-1.5">
            {DOMAIN_QUICK_PILLS.map((pill) => {
              const enabled = isToolAvailable(pill.tool);
              return (
                <button
                  key={pill.tool}
                  disabled={!enabled || loading}
                  onClick={() => handleSendMessage(pill.prompt)}
                  className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                    enabled
                      ? 'border-brand-500/30 bg-brand-500/5 text-brand-700 dark:text-stone-200 hover:bg-brand-500/10 hover:border-brand-500/50'
                      : 'border-stone-300 dark:border-stone-800 text-stone-400 opacity-50 cursor-not-allowed'
                  }`}
                >
                  {pill.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Chat Message Scroll Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] rounded-lg p-3 text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-brand-500 text-white font-medium'
                    : 'bg-paper-dim dark:bg-stone-900 border border-divider dark:border-stone-800 text-ink dark:text-stone-100'
                }`}
              >
                {/* Executed Tool Indicator Badge */}
                {msg.toolInvoked && (
                  <div className="mb-2 flex items-center gap-1.5 text-[10px] font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 w-fit">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Executed: {msg.toolInvoked}</span>
                  </div>
                )}

                {/* Formatted Markdown Content */}
                <div className="whitespace-pre-wrap font-sans space-y-1">
                  {msg.text}
                </div>

                {/* Footer Metadata */}
                <div className="mt-2 flex items-center justify-between text-[10px] opacity-75 pt-1 border-t border-black/5 dark:border-white/5">
                  <span>{msg.timestamp}</span>
                  {msg.tokensUsed !== undefined && (
                    <span className="font-mono ml-3">
                      {msg.tokensUsed} tokens ({msg.latencyMs}ms)
                    </span>
                  )}
                </div>
              </div>

              {msg.sender === 'user' && (
                <div className="w-7 h-7 rounded-full bg-stone-700 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-paper-dim dark:bg-stone-900 border border-divider dark:border-stone-800 rounded-lg p-3 text-xs flex items-center gap-2 text-ink-muted dark:text-stone-400">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-500" />
                <span>Executing 2-step tool call synthesis...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Prompt Input Form */}
        <div className="p-3 border-t border-divider dark:border-stone-800 bg-paper dark:bg-stone-950">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask an operational question (e.g. 'Show attendance for last 30 days')..."
              disabled={loading}
              className="flex-1 bg-paper-dim dark:bg-stone-900 border border-divider dark:border-stone-800 rounded-md px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="p-2 bg-brand-500 text-white rounded-md hover:bg-brand-600 disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="mt-1.5 flex items-center gap-1 text-[10px] text-ink-muted dark:text-stone-500">
            <ShieldAlert className="w-3 h-3 text-brand-500" />
            <span>Zero-Trust 2-Step Function Calling • Read-Only Operational Analytics</span>
          </div>
        </div>
      </div>
    </Drawer>
  );
};
