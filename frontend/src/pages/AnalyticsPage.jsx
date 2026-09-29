import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Gauge, 
  Activity, 
  Car, 
  CloudSun, 
  AlertTriangle,
  RefreshCw,
  Clock
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';
import MetricCard from '../components/MetricCard';
import { api } from '../services/api';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const data = await api.getAnalyticsSummary();
      setAnalytics(data);
    } catch (err) {
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const hourlyData = analytics?.hourly_flow || [];
  const zoneStats = analytics?.zone_stats || {};

  const zoneChartData = Object.keys(zoneStats).map(zoneName => ({
    zone: zoneName,
    vehicles: zoneStats[zoneName].vehicles,
    speed: zoneStats[zoneName].speed_kmh
  }));

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider">
              REAL-TIME URBAN TRAFFIC TELEMETRY
            </span>
          </div>
          <h1 className="text-xl font-black text-slate-100 mt-0.5">Traffic Analytics & Congestion Index</h1>
          <p className="text-xs text-slate-400">
            Hourly vehicle flow rates, zonal density bottlenecks, and environmental velocity distributions.
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center space-x-1.5 transition self-start md:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="City Vehicle Throughput"
          value={`${analytics?.total_vehicles_tracked || '1,420+'}`}
          subtitle="Unique cross-camera tracks"
          icon={Car}
          color="cyan"
          change="+18.4%"
        />
        <MetricCard
          title="Congestion Index"
          value={`${Math.round((analytics?.overall_congestion_index || 0.22) * 100)}%`}
          subtitle="Urban road network load"
          icon={Activity}
          color="amber"
          change="NORMAL"
        />
        <MetricCard
          title="City-Wide Average Speed"
          value={`${analytics?.average_city_speed_kmh || 48.5} km/h`}
          subtitle="Target threshold: >45 km/h"
          icon={Gauge}
          color="emerald"
          change="+3.2 km/h"
        />
        <MetricCard
          title="Environmental Context"
          value={analytics?.weather_condition || 'CLEAR'}
          subtitle="Dynamic OCR penalty active"
          icon={CloudSun}
          color="purple"
          change="OPTIMAL"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Volume & Speed Flow Chart */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              12-Hour Traffic Volume (Vehicles / Hour)
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Real-time Stream</span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourlyData}>
                <defs>
                  <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f2fe" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00f2fe" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="volume" stroke="#00f2fe" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" name="Vehicle Volume" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Zone-by-Zone Velocity Breakdown */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Zone Vehicle Density & Speed (km/h)
            </span>
            <span className="text-[10px] text-slate-500 font-mono">By Corridor</span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="zone" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="vehicles" fill="#a855f7" name="Active Vehicles" radius={[4, 4, 0, 0]} />
                <Bar dataKey="speed" fill="#10b981" name="Avg Speed (km/h)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Corridor Table Breakdown */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 overflow-hidden shadow-xl p-5 space-y-3">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
          Corridor Congestion & Telemetry Health Status
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          {Object.keys(zoneStats).map((zone) => {
            const z = zoneStats[zone];
            return (
              <div key={zone} className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-cyan-400 font-mono">{z.camera_id}</span>
                  <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                    z.status === 'LOW'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : z.status === 'MODERATE'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-red-950 text-red-300 border border-red-800'
                  }`}>
                    {z.status}
                  </span>
                </div>
                <p className="font-semibold text-slate-200">{zone}</p>
                <div className="flex justify-between text-slate-400 text-[11px] pt-1 border-t border-slate-800/80">
                  <span>Vehicles: <strong className="text-slate-200">{z.vehicles}</strong></span>
                  <span>Speed: <strong className="text-emerald-400">{z.speed_kmh} km/h</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
