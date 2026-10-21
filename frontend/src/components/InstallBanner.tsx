import { usePWA } from '../hooks/usePWA';

export function InstallBanner() {
  const { canInstall, isInstalled, install } = usePWA();

  if (isInstalled || !canInstall) return null;

  return (
    <div className="install-banner">
      <span className="install-text">Install Kingdom Agency on your device</span>
      <button className="install-btn" onClick={install}>
        INSTALL
      </button>
    </div>
  );
}
