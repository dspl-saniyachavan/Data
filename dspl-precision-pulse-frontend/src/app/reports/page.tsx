'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import RBACGuard from '@/components/RBACGuard';

interface HealthReport {
  health_score: number;
  health_status: string;
  metrics: {
    recent_events_24h: number;
    recent_failures_24h: number;
    security_events_24h: number;
    connected_devices: number;
  };
}

interface AuditReport {
  summary: {
    total_events: number;
    successful_events: number;
    failed_events: number;
    success_rate: number;
  };
  event_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
}

interface FailureReport {
  summary: {
    total_failures: number;
    critical_failures: number;
    failure_types: number;
  };
  most_common_errors: Array<{ error: string; count: number }>;
}

interface ConfigChangeReport {
  summary: {
    total_changes: number;
    successful_changes: number;
    failed_changes: number;
    success_rate: number;
  };
}

interface OfflineReport {
  summary: {
    total_offline_events: number;
    total_online_events: number;
    affected_devices: number;
  };
}

export default function ReportsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'health' | 'audit' | 'failures' | 'config' | 'offline'>('health');
  
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);
  const [auditReport, setAuditReport] = useState<AuditReport | null>(null);
  const [failureReport, setFailureReport] = useState<FailureReport | null>(null);
  const [configReport, setConfigReport] = useState<ConfigChangeReport | null>(null);
  const [offlineReport, setOfflineReport] = useState<OfflineReport | null>(null);
  
  const [reportDays, setReportDays] = useState(7);
  const [retentionStats, setRetentionStats] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');

    if (!token) {
      router.push('/login');
      return;
    }

    if (userData) {
      setUser(JSON.parse(userData));
    }

    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load health report
      const healthRes = await fetch(`http://localhost:5000/api/reports/system-health`, { headers });
      if (healthRes.ok) {
        const data = await healthRes.json();
        setHealthReport(data.report);
      }

      // Load audit report
      const auditRes = await fetch(`http://localhost:5000/api/reports/audit?days=${reportDays}`, { headers });
      if (auditRes.ok) {
        const data = await auditRes.json();
        setAuditReport(data.report);
      }

      // Load failure report
      const failureRes = await fetch(`http://localhost:5000/api/reports/failures?days=${reportDays}`, { headers });
      if (failureRes.ok) {
        const data = await failureRes.json();
        setFailureReport(data.report);
      }

      // Load config change report
      const configRes = await fetch(`http://localhost:5000/api/reports/config-changes?days=${reportDays}`, { headers });
      if (configRes.ok) {
        const data = await configRes.json();
        setConfigReport(data.report);
      }

      // Load offline events report
      const offlineRes = await fetch(`http://localhost:5000/api/reports/offline-events?days=${reportDays}`, { headers });
      if (offlineRes.ok) {
        const data = await offlineRes.json();
        setOfflineReport(data.report);
      }

      // Load retention statistics
      const retentionRes = await fetch(`http://localhost:5000/api/reports/retention/statistics`, { headers });
      if (retentionRes.ok) {
        const data = await retentionRes.json();
        setRetentionStats(data.statistics);
      }
    } catch (err) {
      console.error('Error loading reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    document.cookie = 'token=; path=/; max-age=0';
    window.location.href = '/login';
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 50) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-gray-300 border-b border-gray-400 sticky top-0 z-50">
        <div className="px-4 sm:px-8 py-4 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex items-center gap-4">
            <img src="/logo.svg" alt="PrecisionPulse Logo" className="w-8 h-8 sm:w-12 sm:h-12" />
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-slate-900">Reports & Analytics</h1>
              <p className="text-xs sm:text-sm text-slate-600">System Health & Audit Logs</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3 w-full lg:w-auto">
            <button onClick={() => router.push('/dashboard')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm">
              Dashboard
            </button>
            <button onClick={() => router.push('/profile')} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold text-sm">
              Profile
            </button>
            <button onClick={handleLogout} className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-white hover:bg-gray-100 text-red-600 rounded-lg font-semibold text-sm border border-gray-300">
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 sm:px-8 lg:px-20 py-12">
        <div className="mb-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-2">System Reports</h2>
          <p className="text-gray-400 text-base sm:text-lg">Monitor system health, audit logs, and performance metrics</p>
        </div>

        {/* Report Period Selector */}
        <div className="mb-8 flex gap-4 items-center">
          <label className="text-white font-semibold">Report Period:</label>
          <select 
            value={reportDays} 
            onChange={(e) => {
              setReportDays(parseInt(e.target.value));
              loadReports();
            }}
            className="px-4 py-2 rounded-lg border border-gray-300 bg-white text-slate-900"
          >
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <button 
            onClick={loadReports}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold"
          >
            Refresh
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 flex flex-wrap gap-2 border-b border-gray-600">
          {[
            { id: 'health', label: 'System Health' },
            { id: 'audit', label: 'Audit Summary' },
            { id: 'failures', label: 'Failures' },
            { id: 'config', label: 'Config Changes' },
            { id: 'offline', label: 'Offline Events' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 font-semibold border-b-2 transition ${
                activeTab === tab.id
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center text-gray-400 py-12">Loading reports...</div>
        ) : (
          <>
            {/* System Health Tab */}
            {activeTab === 'health' && healthReport && (
              <div className="space-y-6">
                <div className={`${getHealthBgColor(healthReport.health_score)} rounded-lg p-8 border-l-4 ${
                  healthReport.health_score >= 80 ? 'border-green-600' :
                  healthReport.health_score >= 50 ? 'border-yellow-600' :
                  'border-red-600'
                }`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-slate-900">System Health Score</h3>
                    <div className={`text-5xl font-bold ${getHealthColor(healthReport.health_score)}`}>
                      {healthReport.health_score.toFixed(0)}
                    </div>
                  </div>
                  <p className={`text-lg font-semibold ${getHealthColor(healthReport.health_score)}`}>
                    Status: {healthReport.health_status.toUpperCase()}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Events (24h)</p>
                    <p className="text-3xl font-bold text-slate-900">{healthReport.metrics.recent_events_24h}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Failures (24h)</p>
                    <p className="text-3xl font-bold text-red-600">{healthReport.metrics.recent_failures_24h}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Security Events (24h)</p>
                    <p className="text-3xl font-bold text-orange-600">{healthReport.metrics.security_events_24h}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Connected Devices</p>
                    <p className="text-3xl font-bold text-green-600">{healthReport.metrics.connected_devices}</p>
                  </div>
                </div>

                {retentionStats && (
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <h4 className="text-xl font-bold text-slate-900 mb-4">Log Retention Status</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-gray-600 text-sm mb-2">Total Logs</p>
                        <p className="text-2xl font-bold text-slate-900">{retentionStats.total_logs}</p>
                      </div>
                      <div>
                        <p className="text-gray-600 text-sm mb-2">Expired Logs</p>
                        <p className="text-2xl font-bold text-red-600">{retentionStats.expired_logs}</p>
                      </div>
                      <div>
                        <p className="text-gray-600 text-sm mb-2">Expiring Soon (7 days)</p>
                        <p className="text-2xl font-bold text-yellow-600">{retentionStats.expiring_soon}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Audit Summary Tab */}
            {activeTab === 'audit' && auditReport && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Total Events</p>
                    <p className="text-3xl font-bold text-slate-900">{auditReport.summary.total_events}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Successful</p>
                    <p className="text-3xl font-bold text-green-600">{auditReport.summary.successful_events}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Failed</p>
                    <p className="text-3xl font-bold text-red-600">{auditReport.summary.failed_events}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Success Rate</p>
                    <p className="text-3xl font-bold text-blue-600">{auditReport.summary.success_rate.toFixed(1)}%</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <h4 className="text-lg font-bold text-slate-900 mb-4">Event Distribution</h4>
                    <div className="space-y-2">
                      {Object.entries(auditReport.event_distribution).map(([event, count]) => (
                        <div key={event} className="flex justify-between items-center">
                          <span className="text-gray-600">{event}</span>
                          <span className="font-bold text-slate-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <h4 className="text-lg font-bold text-slate-900 mb-4">Severity Distribution</h4>
                    <div className="space-y-2">
                      {Object.entries(auditReport.severity_distribution).map(([severity, count]) => (
                        <div key={severity} className="flex justify-between items-center">
                          <span className="text-gray-600 capitalize">{severity}</span>
                          <span className="font-bold text-slate-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Failures Tab */}
            {activeTab === 'failures' && failureReport && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Total Failures</p>
                    <p className="text-3xl font-bold text-red-600">{failureReport.summary.total_failures}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Critical Failures</p>
                    <p className="text-3xl font-bold text-orange-600">{failureReport.summary.critical_failures}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Failure Types</p>
                    <p className="text-3xl font-bold text-slate-900">{failureReport.summary.failure_types}</p>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-6 shadow-lg">
                  <h4 className="text-lg font-bold text-slate-900 mb-4">Most Common Errors</h4>
                  <div className="space-y-3">
                    {failureReport.most_common_errors.map((error, idx) => (
                      <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                        <span className="text-gray-700">{error.error}</span>
                        <span className="font-bold text-red-600">{error.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Config Changes Tab */}
            {activeTab === 'config' && configReport && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Total Changes</p>
                    <p className="text-3xl font-bold text-slate-900">{configReport.summary.total_changes}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Successful</p>
                    <p className="text-3xl font-bold text-green-600">{configReport.summary.successful_changes}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Failed</p>
                    <p className="text-3xl font-bold text-red-600">{configReport.summary.failed_changes}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Success Rate</p>
                    <p className="text-3xl font-bold text-blue-600">{configReport.summary.success_rate.toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Offline Events Tab */}
            {activeTab === 'offline' && offlineReport && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Offline Events</p>
                    <p className="text-3xl font-bold text-red-600">{offlineReport.summary.total_offline_events}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Online Events</p>
                    <p className="text-3xl font-bold text-green-600">{offlineReport.summary.total_online_events}</p>
                  </div>
                  <div className="bg-white rounded-lg p-6 shadow-lg">
                    <p className="text-gray-600 text-sm font-semibold mb-2">Affected Devices</p>
                    <p className="text-3xl font-bold text-slate-900">{offlineReport.summary.affected_devices}</p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
