import React from 'react';

const createSwapComponent = () => (props: any) => <span {...props} />;

export const SwapOn = createSwapComponent();
export const SwapOff = createSwapComponent();

