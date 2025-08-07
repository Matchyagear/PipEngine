import React from 'react';

const Logo = ({ size = "md", showText = true }) => {
    const sizeClasses = {
        sm: "w-8 h-8 text-sm",
        md: "w-10 h-10 text-lg",
        lg: "w-12 h-12 text-xl"
    };

    return (
        <div className="flex items-center space-x-3">
            <div className={`${sizeClasses[size]} bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center`}>
                <span className="text-white font-bold">SB</span>
            </div>
            {showText && (
                <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        Financial Dashboard
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        Enhanced Trading Platform
                    </p>
                </div>
            )}
        </div>
    );
};

export default Logo;
