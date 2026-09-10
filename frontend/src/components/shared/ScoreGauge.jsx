import React from "react";

export function ScoreGauge({ score = 0, size = 120, strokeWidth = 10 }) {
  const normalizedScore = Math.min(100, Math.max(0, Number(score) || 0));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let color = "#10b981"; // Emerald
  let label = "Compliant";

  if (normalizedScore < 60) {
    color = "#ef4444"; // Red
    label = "Non-Compliant";
  } else if (normalizedScore < 80) {
    color = "#f59e0b"; // Amber
    label = "Review Needed";
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#e2e8f0"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {normalizedScore.toFixed(0)}%
          </span>
          <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
            Score
          </span>
        </div>
      </div>
      <span className="mt-2 text-xs font-semibold uppercase tracking-wider" style={{ color }}>
        {label}
      </span>
    </div>
  );
}
