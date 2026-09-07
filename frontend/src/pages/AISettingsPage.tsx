import React, { useState, useEffect } from 'react';
import {
  Cpu,
  ShieldCheck,
  Zap,
  Activity,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Database,
  Lock,
} from 'lucide-react';
import { aiApi } from '../services/api/aiApi';
import type {
  AIProviderConfig,
  AIUsageStats,
  AIAuditLogQueryResponse,
  AIAuditLogItem,
} from '../api/ai';

export const AISettingsPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [savingConfig, setSavingConfig] = useState<boolean>(false);
  const [savingQuota, setSavingQuota] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Stats & Config state
  const [usageStats, setUsageStats] = useState<AIUsageStats | null>(null);
  const [providerConfig, setProviderConfig] = useState<AIProviderConfig | null>(null);
  const [auditLogs, setAuditLogs] = useState<AIAuditLogQueryResponse | null>(null);

  // Form states
  const [providerType, setProviderType] = useState<string>('MOCK');
  const [modelName, setModelName] = useState<string>('mock-default-v1');
  const [allowExternal, setAllowExternal] = useState<boolean>(false);
  const [isEnabled, setIsEnabled] = useState<boolean>(true);
  const [notes, setNotes] = useState<string>('');

  // Quota form state
  const [quotaInput, setQuotaInput] = useState<number>(1000000);

  // Audit filter states
  const [filterCapability, setFilterCapability] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, configRes, logsRes] = await Promise.all([
        aiApi.getUsageStats(),
        aiApi.getProviderConfig(),
        aiApi.getAuditLogs({
          capability: filterCapability || undefined,
          status: filterStatus || undefined,
          limit: 50,
        }),
      ]);

      setUsageStats(statsRes);
      setQuotaInput(statsRes.monthly_token_quota);

      setProviderConfig(configRes);
      setProviderType(configRes.provider_type);
      setModelName(configRes.model_name || 'mock-default-v1');
      setAllowExternal(configRes.allow_external_ai);
      setIsEnabled(configRes.is_enabled);
      setNotes(configRes.notes || '');

      setAuditLogs(logsRes);
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || 'Failed to load AI administration settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterCapability, filterStatus]);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingConfig(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await aiApi.updateProviderConfig({
        provider_type: providerType,
        model_name: modelName,
        allow_external_ai: allowExternal,
        is_enabled: isEnabled,
        notes: notes,
      });
      setProviderConfig(updated);
      setSuccessMsg('AI Provider Configuration updated successfully.');
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || 'Failed to update provider configuration.');
    } finally {
      setSavingConfig(false);
    }
  };

  const handleUpdateQuota = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingQuota(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updatedStats = await aiApi.updateUsageLimit({
        monthly_token_quota: Number(quotaInput),
        is_enabled: isEnabled,
      });
      setUsageStats(updatedStats);
      setSuccessMsg('Monthly AI token quota updated successfully.');
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || 'Failed to update monthly token quota.');
    } finally {
      setSavingQuota(false);
    }
  };

  const usedPct = usageStats
    ? Math.min(100, Math.round((usageStats.used_tokens_current_month / usageStats.monthly_token_quota) * 100))
    : 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Cpu className="w-7 h-7 text-indigo-600" />
            AI Subsystem Administration & Governance
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage provider selection, zero-trust cloud dispatches, per-tenant token quotas, and system audit logs.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Status
        </button>
      </div>

      {/* Notifications */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-500" />
          <span className="text-sm">{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-700 p-4 rounded-xl flex items-center gap-3">
          <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-500" />
          <span className="text-sm">{successMsg}</span>
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Card 1: Token Usage */}
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Monthly Token Quota</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {usageStats ? usageStats.used_tokens_current_month.toLocaleString() : '0'} /{' '}
              {usageStats ? usageStats.monthly_token_quota.toLocaleString() : '0'}
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  usedPct > 90 ? 'bg-red-500' : usedPct > 70 ? 'bg-amber-500' : 'bg-indigo-600'
                }`}
                style={{ width: `${usedPct}%` }}
              />
            </div>
          </div>
          <div className="text-xs text-gray-500 flex justify-between">
            <span>{usedPct}% Consumed</span>
            <span>Resets {usageStats?.quota_reset_date || 'N/A'}</span>
          </div>
        </div>

        {/* Card 2: Active Provider */}
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Active AI Provider</span>
            <Cpu className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-900">{providerConfig?.provider_type || 'MOCK'}</div>
            <div className="text-xs text-gray-500 mt-1">{providerConfig?.model_name || 'mock-default-v1'}</div>
          </div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Operational
          </div>
        </div>

        {/* Card 3: Privacy & Cloud Toggle */}
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Data Privacy Mode</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <div className="text-xl font-bold text-gray-900">
              {allowExternal ? 'Cloud Dispatches' : 'Zero-Cloud Local'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {allowExternal ? 'External API dispatches allowed' : '100% On-prem / Local Mock execution'}
            </div>
          </div>
          <div
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
              allowExternal ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'
            }`}
          >
            {allowExternal ? <Zap className="w-3 h-3" /> : <Lock className="w-3 h-3" />}
            {allowExternal ? 'External API' : 'Zero Data Leakage'}
          </div>
        </div>

        {/* Card 4: Audit Activity */}
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-gray-500">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Audit Events</span>
            <Activity className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">{auditLogs?.total_count || 0}</div>
            <div className="text-xs text-gray-500 mt-1">
              Est. Cost: ${auditLogs ? auditLogs.total_cost_usd.toFixed(4) : '0.0000'} USD
            </div>
          </div>
          <div className="text-xs text-gray-500">
            Tokens: {auditLogs ? (auditLogs.total_prompt_tokens + auditLogs.total_completion_tokens).toLocaleString() : 0}
          </div>
        </div>
      </div>

      {/* Main Administrative Form Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Panel 1: Provider Config Form */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              Provider & Privacy Settings
            </h2>
            <span className="text-xs text-gray-400">Scoped to school tenant</span>
          </div>

          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Provider Type
                </label>
                <select
                  value={providerType}
                  onChange={(e) => setProviderType(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="MOCK">MOCK (Deterministic Mock Provider)</option>
                  <option value="GEMINI">GEMINI (Google Gemini 1.5 Flash)</option>
                  <option value="OPENAI">OPENAI (OpenAI GPT-4o-mini)</option>
                  <option value="ANTHROPIC">ANTHROPIC (Claude 3.5 Sonnet)</option>
                  <option value="LOCAL_ORTOOLS">LOCAL_ORTOOLS (Local Constraint Solver)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Model Identifier
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="e.g. gemini-1.5-flash"
                  className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Toggles */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
                <div>
                  <div className="text-sm font-semibold text-gray-900">Allow External Cloud AI</div>
                  <div className="text-xs text-gray-500">Enable dispatches to cloud LLM APIs</div>
                </div>
                <input
                  type="checkbox"
                  checked={allowExternal}
                  onChange={(e) => setAllowExternal(e.target.checked)}
                  className="w-5 h-5 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
                <div>
                  <div className="text-sm font-semibold text-gray-900">AI Subsystem Active</div>
                  <div className="text-xs text-gray-500">Global enable/disable toggle</div>
                </div>
                <input
                  type="checkbox"
                  checked={isEnabled}
                  onChange={(e) => setIsEnabled(e.target.checked)}
                  className="w-5 h-5 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Administrative Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                placeholder="Notes regarding AI configuration policy..."
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                disabled={savingConfig}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-xl shadow-sm transition disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {savingConfig ? 'Saving Config...' : 'Save Provider Settings'}
              </button>
            </div>
          </form>
        </div>

        {/* Panel 2: Quota & Token Limits */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
          <div className="border-b border-gray-100 pb-4">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Monthly Token Limit
            </h2>
            <p className="text-xs text-gray-500 mt-1">Configure monthly quota cap for tenant.</p>
          </div>

          <form onSubmit={handleUpdateQuota} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                Monthly Token Quota
              </label>
              <input
                type="number"
                value={quotaInput}
                onChange={(e) => setQuotaInput(Number(e.target.value))}
                min={0}
                step={50000}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <span className="text-xs text-gray-400 mt-1 block">Default limit: 1,000,000 tokens</span>
            </div>

            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
              <div className="font-semibold">Quota Reset Schedule</div>
              <div>Current month resets on {usageStats?.quota_reset_date || 'N/A'}.</div>
            </div>

            <button
              type="submit"
              disabled={savingQuota}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 hover:bg-black text-white font-medium text-sm rounded-xl transition disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {savingQuota ? 'Updating Quota...' : 'Update Monthly Quota'}
            </button>
          </form>
        </div>
      </div>

      {/* System AI Audit Trail Table */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-purple-600" />
              System AI Operation Audit Log
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              Immutable audit records tracking capability calls, token usage, latency, and cost dispatches.
            </p>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3">
            <select
              value={filterCapability}
              onChange={(e) => setFilterCapability(e.target.value)}
              className="rounded-xl border border-gray-300 px-3 py-1.5 text-xs text-gray-700"
            >
              <option value="">All Capabilities</option>
              <option value="ASSISTANT">ASSISTANT</option>
              <option value="TIMETABLE">TIMETABLE</option>
              <option value="RISK">RISK</option>
              <option value="COMMUNICATION">COMMUNICATION</option>
              <option value="REPORT_CARD">REPORT_CARD</option>
            </select>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="rounded-xl border border-gray-300 px-3 py-1.5 text-xs text-gray-700"
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="ERROR">ERROR</option>
              <option value="BLOCKED">BLOCKED</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-600">
            <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">User</th>
                <th className="p-3">Capability</th>
                <th className="p-3">Provider / Model</th>
                <th className="p-3 text-right">Tokens</th>
                <th className="p-3 text-right">Cost ($)</th>
                <th className="p-3 text-right">Latency</th>
                <th className="p-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {auditLogs?.items && auditLogs.items.length > 0 ? (
                auditLogs.items.map((log: AIAuditLogItem) => (
                  <tr key={log.id} className="hover:bg-gray-50/50 transition">
                    <td className="p-3 font-mono text-gray-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-3 font-medium text-gray-900 whitespace-nowrap">{log.user_full_name}</td>
                    <td className="p-3 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded-full font-semibold text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {log.capability}
                      </span>
                    </td>
                    <td className="p-3 whitespace-nowrap text-gray-700">
                      {log.provider_type} / <span className="text-gray-400">{log.model_name || 'N/A'}</span>
                    </td>
                    <td className="p-3 text-right font-mono font-medium text-gray-800">
                      {log.total_tokens.toLocaleString()}
                    </td>
                    <td className="p-3 text-right font-mono text-gray-600">${log.estimated_cost_usd.toFixed(4)}</td>
                    <td className="p-3 text-right font-mono text-gray-500">{log.latency_ms} ms</td>
                    <td className="p-3 text-center whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-red-50 text-red-700 border border-red-200'
                        }`}
                      >
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-gray-400 italic">
                    No AI audit log events found matching criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AISettingsPage;
