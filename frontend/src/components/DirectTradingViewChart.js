import React from 'react';

const DirectTradingViewChart = ({ symbol, width = '100%', height = 80 }) => {
    // Direct iframe embed - no JavaScript complexity
    const tradingViewUrl = `https://s.tradingview.com/widgetembed/?frameElementId=tradingview_${symbol}&symbol=${symbol}&interval=D&hidesidetoolbar=1&hidetoptoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&hideideas=1&theme=dark&style=1&timezone=Etc%2FUTC&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en&utm_source=&utm_medium=widget&utm_campaign=chart&utm_term=${symbol}`;

    return (
        <iframe
            src={tradingViewUrl}
            width={width}
            height={height}
            style={{
                border: 'none',
                borderRadius: '4px',
                backgroundColor: '#1f2937'
            }}
            frameBorder="0"
            allowTransparency="true"
            scrolling="no"
            allowFullScreen={true}
            title={`${symbol} Chart`}
        />
    );
};

export default DirectTradingViewChart;
