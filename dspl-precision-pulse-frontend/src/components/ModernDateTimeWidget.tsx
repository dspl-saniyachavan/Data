import { useEffect, useState } from 'react';

export default function ModernDateTimeWidget() {
  const [time, setTime] = useState<{
    day: string;
    date: string;
    hours: string;
    minutes: string;
    seconds: string;
    period: string;
  }>({
    day: '',
    date: '',
    hours: '',
    minutes: '',
    seconds: '',
    period: ''
  });

  useEffect(() => {
    const updateDateTime = () => {
      const now = new Date();
      
      // Get day
      const dayStr = now.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
      
      // Get date
      const dateStr = now.toLocaleDateString('en-US', { day: '2-digit', month: 'short' }).toUpperCase();
      
      // Get time in 12-hour format
      let hours = now.getHours();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      const period = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      if (hours === 0) hours = 12;
      
      setTime({
        day: dayStr,
        date: dateStr,
        hours: String(hours).padStart(2, '0'),
        minutes: String(minutes).padStart(2, '0'),
        seconds: String(seconds).padStart(2, '0'),
        period: period
      });
    };

    updateDateTime();
    const interval = setInterval(updateDateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center justify-between gap-8 px-6 py-3 bg-gradient-to-br from-indigo-500 via-purple-500 to-purple-600 rounded-3xl shadow-lg" style={{ minWidth: 'fit-content' }}>
      {/* Left side - Date and Day */}
      <div className="flex flex-col items-center gap-1">
        <div className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-lg">
          <span className="text-white font-bold text-xs tracking-wide">
            {time.day} → {time.date}
          </span>
        </div>
      </div>

      {/* Center - Time with seconds */}
      <div className="flex flex-col items-center gap-0">
        <div className="flex items-baseline gap-1">
          <span className="text-white font-bold text-5xl tracking-tight leading-none">
            {time.hours}:{time.minutes}
          </span>
          <span className="text-white font-semibold text-xs">
            {time.period}
          </span>
        </div>
        <span className="text-white/80 font-semibold text-xs tracking-tight">
          {time.seconds}
        </span>
      </div>

      {/* Right side - Empty for balance */}
      <div className="w-20"></div>
    </div>
  );
}
