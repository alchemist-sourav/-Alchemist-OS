import React from 'react';
import { AICoreOrb } from './AICoreOrb';

export const AlchemistCore = () => {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
      <div className="w-[500px] h-[500px]">
        <AICoreOrb />
      </div>
    </div>
  );
};
