import React, { useMemo } from 'react';

const Sparkline = ({ data = [], width = 120, height = 28, stroke = '#22c55e', strokeWidth = 2, fill = 'none' }) => {
    const path = useMemo(() => {
        if (!data || data.length === 0) return '';
        const min = Math.min(...data);
        const max = Math.max(...data);
        const span = max - min || 1;
        const stepX = width / (data.length - 1);
        return data
            .map((v, i) => {
                const x = i * stepX;
                const y = height - ((v - min) / span) * height;
                return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
            })
            .join(' ');
    }, [data, width, height]);

    return (
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
            {fill !== 'none' && (
                <path d={`${path} L ${width},${height} L 0,${height} Z`} fill={fill} opacity="0.2" />
            )}
            <path d={path} fill="none" stroke={stroke} strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
    );
};

export default Sparkline;
