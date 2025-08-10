import React from 'react';

const Logo = ({ size = "md", showText = true, src = "/logo512.png" }) => {
  const sizeClasses = {
    sm: "w-16 h-16",
    md: "w-20 h-20",
    lg: "w-24 h-24"
  };

  return (
    <div className="flex items-center space-x-2 ml-1 sm:ml-2">
      <div className={`${sizeClasses[size]} rounded-md overflow-hidden flex items-center justify-center`}>
        <img src={src} alt="PipEngine Logo" className="object-cover w-full h-full" />
      </div>
      {showText && (
        <div className="hidden sm:block">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">PIPENGINE.COM</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">Financial Dashboard</p>
        </div>
      )}
    </div>
  );
};

export default Logo;
