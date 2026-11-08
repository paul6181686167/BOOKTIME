import React from 'react';

// Composant compteur animé
const AnimatedCounter = ({ value, className }) => {
  const [displayed, setDisplayed] = React.useState(0);
  React.useEffect(() => {
    if (value === 0) { setDisplayed(0); return; }
    if (!value) return;
    let start = 0;
    const step = Math.ceil(value / 20);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplayed(value); clearInterval(timer); }
      else setDisplayed(start);
    }, 30);
    return () => clearInterval(timer);
  }, [value]);
  return <span className={className}>{displayed}</span>;
};

export default AnimatedCounter;
