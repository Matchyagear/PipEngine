import React from 'react';

const Logo = ({ size = "md", showText = true, src = "/logo512.png" }) => {
  const sizeClasses = {
    sm: "w-24 h-10",
    md: "w-36 h-14",
    lg: "w-48 h-16"
  };

  return (
    <div className="flex items-center space-x-3 ml-2 sm:ml-3">
      <div className={`${sizeClasses[size]} rounded-md overflow-hidden flex items-center`}>
        <img src={src} alt="PipEngine Logo" className="object-contain w-full h-full" />
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
