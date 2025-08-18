import React from 'react';

const CustomTradingViewChart = ({
    chartUrl,
    width = '100%',
    height = 192,
    title = "Custom Chart",
    symbol = "SPY"
}) => {
    return (
        <div className="w-full h-full">
            <iframe
                src={chartUrl}
                width={width}
                height={height}
                style={{
                    border: 'none',
                    borderRadius: '8px',
                    backgroundColor: '#1f2937'
                }}
                frameBorder="0"
                allowTransparency="true"
                scrolling="no"
                allowFullScreen={true}
                title={`${symbol} Custom Chart`}
            />
        </div>
    );
};

export default CustomTradingViewChart;
