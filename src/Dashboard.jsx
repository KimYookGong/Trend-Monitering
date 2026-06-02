import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowUp, ArrowDown, TrendingUp, AlertTriangle, Radio } from 'lucide-react';

// 예시 데이터 및 초기 트렌드 목록
const INITIAL_TRENDS = [
  { rank: 1, keyword: 'Generative AI', count: 120, prevRank: 1, trend: 'stable' },
  { rank: 2, keyword: 'RAG Systems', count: 98, prevRank: 4, trend: 'up' },
  { rank: 3, keyword: 'Agentic Workflows', count: 85, prevRank: 2, trend: 'down' },
  { rank: 4, keyword: 'Vector Database', count: 72, prevRank: 3, trend: 'down' },
  { rank: 5, keyword: 'Multimodal Models', count: 64, prevRank: 5, trend: 'stable' },
];

export default function TrendDashboard() {
  const [trends, setTrends] = useState(INITIAL_TRENDS);
  const [chartData, setChartData] = useState([
    { time: '09:00', count: 150 },
    { time: '10:00', count: 180 },
    { time: '11:00', count: 240 },
    { time: '12:00', count: 220 },
    { time: '13:00', count: 310 },
  ]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    // 실시간 SSE(Server-Sent Events) 연결 수립
    // 백엔드의 FastAPI/Express 엔드포인트 URL에 매핑합니다.
    const eventSource = new EventSource('http://localhost:8000/api/trends/stream');

    eventSource.onopen = () => {
      setIsConnected(true);
      console.log('SSE Stream Connection Established!');
    };

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // 1. 실시간 차트 업데이트 (시간 경과 데이터 누적 및 부드러운 갱신)
      if (data.chartPoint) {
        setChartData((prev) => [...prev.slice(1), data.chartPoint]);
      }
      
      // 2. 실시간 트렌드 순위 데이터 업데이트
      if (data.trends) {
        setTrends((prevTrends) => {
          // 각 트렌드의 순위 변동 여부(prevRank)를 파악해 아이콘 및 변동 방향 설정
          return data.trends.map((newTrend, index) => {
            const oldTrend = prevTrends.find(t => t.keyword === newTrend.keyword);
            const prevRank = oldTrend ? oldTrend.rank : index + 1;
            let trend = 'stable';
            if (prevRank > index + 1) trend = 'up';
            else if (prevRank < index + 1) trend = 'down';
            
            return {
              ...newTrend,
              rank: index + 1,
              prevRank,
              trend
            };
          });
        });
      }
      
      setLastUpdated(new Date().toLocaleTimeString());
    };

    eventSource.onerror = (err) => {
      console.error('SSE Connection Error:', err);
      setIsConnected(false);
      eventSource.close();
    };

    // 로컬 브라우저 단독 데모를 위해 SSE가 연결되지 않을 시 가상의 Mock 수집기를 실행합니다.
    const mockInterval = setInterval(() => {
      if (!isConnected) {
        // 가상의 실시간 데이터 업데이트 발생
        setTrends((prevTrends) => {
          const updated = prevTrends.map((t) => {
            // 빈도수 랜덤 변동
            const countChange = Math.floor(Math.random() * 21) - 10;
            return { ...t, count: Math.max(10, t.count + countChange) };
          });
          
          // count가 높은 순서대로 재정렬 (순위 실시간 뒤바뀜 효과 극대화)
          const sorted = [...updated].sort((a, b) => b.count - a.count);
          return sorted.map((t, idx) => {
            const prevRank = t.rank;
            let trend = 'stable';
            if (prevRank > idx + 1) trend = 'up';
            else if (prevRank < idx + 1) trend = 'down';
            return { ...t, rank: idx + 1, prevRank, trend };
          });
        });

        // 실시간 차트 변화 누적
        setChartData((prev) => {
          const nextTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          const nextCount = Math.floor(Math.random() * 150) + 150;
          return [...prev.slice(1), { time: nextTime, count: nextCount }];
        });
        setLastUpdated(new Date().toLocaleTimeString());
      }
    }, 4000);

    return () => {
      eventSource.close();
      clearInterval(mockInterval);
    };
  }, [isConnected]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans selection:bg-teal-500 selection:text-slate-900">
      {/* 최상단 헤더 */}
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between mb-10 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="text-teal-400 w-8 h-8 animate-pulse" />
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-400 to-indigo-500 bg-clip-text text-transparent">
              Anti-Gravity AI 트렌드 라이브 모니터
            </h1>
          </div>
          <p className="text-slate-400 text-sm">
            RSS 및 API 실시간 연동을 통한 최신 연구 동향 및 소셜 버즈 급증 이상 징후 추적
          </p>
        </div>

        {/* 연결 상태 표시 뱃지 */}
        <div className="flex items-center gap-4 bg-slate-900/60 border border-slate-800 rounded-full px-5 py-2.5 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <span className={`relative flex h-3 w-3`}>
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
              <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
            <span className="text-xs font-semibold text-slate-300">
              {isConnected ? 'LIVE STREAM CONNECTED' : 'DEMO MOCK ACTIVE'}
            </span>
          </div>
          {lastUpdated && (
            <span className="text-xs text-slate-500 border-l border-slate-800 pl-4">
              수신시간: {lastUpdated}
            </span>
          )}
        </div>
      </div>

      {/* 대시보드 그리드 */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* 좌측: 실시간 순위 리스트 (Layout Animation 활용) */}
        <div className="lg:col-span-7 bg-slate-900/40 border border-slate-900/80 rounded-2xl p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-teal-500 to-transparent opacity-60"></div>
          
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Radio className="text-rose-500 w-5 h-5 animate-pulse" />
              급상승 실시간 랭킹
            </h2>
            <span className="text-xs text-slate-400">4초마다 자동 순위 보정</span>
          </div>

          <div className="space-y-4">
            {/* AnimatePresence 및 layout prop을 통해 순위 변동 시 리스트 카드들이 부드럽게 위아래로 스왑됨 */}
            <AnimatePresence mode="popLayout">
              {trends.map((item) => (
                <motion.div
                  key={item.keyword}
                  layout // 이 속성이 순위 변동 시 위치를 플립하여 물리적으로 부드럽게 이동시킵니다
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  className="flex items-center justify-between p-4 bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-xl transition-all duration-300 shadow-lg hover:shadow-teal-950/20 group"
                >
                  <div className="flex items-center gap-4">
                    {/* 순위 마크 */}
                    <div className="w-8 h-8 rounded-lg bg-slate-850 flex items-center justify-center font-bold text-teal-400 border border-slate-800 group-hover:bg-teal-500 group-hover:text-slate-950 transition-colors duration-300">
                      {item.rank}
                    </div>
                    {/* 키워드 */}
                    <div>
                      <span className="font-semibold text-slate-200 group-hover:text-white transition-colors duration-300">
                        {item.keyword}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* 언급량 */}
                    <div className="text-right">
                      <span className="block text-sm font-bold text-slate-300 group-hover:text-teal-400 transition-colors">
                        {item.count} 회
                      </span>
                      <span className="block text-[10px] text-slate-500">Hourly count</span>
                    </div>

                    {/* 등락 아이콘 (Framer Motion 스케일 애니메이션 가미) */}
                    <div className="w-16 flex justify-end">
                      {item.trend === 'up' && (
                        <motion.span 
                          initial={{ scale: 0.8 }} 
                          animate={{ scale: [1, 1.2, 1] }} 
                          className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-950/50 border border-emerald-900/50 px-2 py-1 rounded"
                        >
                          <ArrowUp className="w-3.5 h-3.5 animate-bounce" /> UP
                        </motion.span>
                      )}
                      {item.trend === 'down' && (
                        <motion.span 
                          initial={{ scale: 0.8 }} 
                          animate={{ scale: [1, 1.2, 1] }} 
                          className="flex items-center gap-1 text-xs font-bold text-rose-400 bg-rose-950/50 border border-rose-900/50 px-2 py-1 rounded"
                        >
                          <ArrowDown className="w-3.5 h-3.5" /> DOWN
                        </motion.span>
                      )}
                      {item.trend === 'stable' && (
                        <span className="text-xs font-semibold text-slate-500 px-2 py-1">
                          -
                        </span>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* 우측: 시계열 차트 및 이상 감지 경보 로그 */}
        <div className="lg:col-span-5 flex flex-col gap-8">
          
          {/* 우측 상단: 실시간 트렌드 시계열 분석 차트 */}
          <div className="bg-slate-900/40 border border-slate-900/80 rounded-2xl p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-500 to-transparent opacity-60"></div>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              실시간 전체 트렌드 활성도 (Buzz)
            </h2>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#2dd4bf" 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorCount)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 우측 하단: 이상 징후 알림 콘솔 */}
          <div className="bg-slate-900/40 border border-slate-900/80 rounded-2xl p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden flex-1">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-rose-500 to-transparent opacity-60"></div>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-rose-400">
              <AlertTriangle className="w-5 h-5 animate-pulse" />
              실시간 이상 징후 탐지 로그
            </h2>
            <div className="space-y-3">
              <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg">
                <div className="flex justify-between text-xs text-rose-400 font-bold mb-1">
                  <span>🚨 ANOMALY DETECTED</span>
                  <span>10:32 AM</span>
                </div>
                <p className="text-sm text-slate-300">
                  키워드 <span className="text-rose-300 font-semibold">'Agentic Workflows'</span>의 소셜 언급량이 전 시간 대비 <strong className="text-rose-400">225% 급증</strong>하였습니다.
                </p>
                <span className="inline-block mt-2 text-[10px] bg-rose-900/60 px-2 py-0.5 rounded text-rose-250">
                  Slack Webhook 발송됨
                </span>
              </div>

              <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-lg">
                <div className="flex justify-between text-xs text-slate-400 font-bold mb-1">
                  <span>INFO</span>
                  <span>09:00 AM</span>
                </div>
                <p className="text-sm text-slate-400">
                  매일 자정 급상승 키워드 TF-IDF 배치 작업이 안전하게 완료되었습니다.
                </p>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
