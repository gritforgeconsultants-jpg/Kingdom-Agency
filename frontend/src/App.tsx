import { InstallBanner } from './components/InstallBanner';
import { useServiceWorker } from './hooks/useServiceWorker';

function App() {
  useServiceWorker();

  return (
    <div className="app">
      <InstallBanner />
      <header className="hero">
        <div className="badge-icon">🛡️</div>
        <h1>KINGDOM AGENCY</h1>
        <p className="subtitle">Your mission awaits, Agent.</p>
        <p className="verse">
          "The word of our God shall stand for ever."
          <br />
          <span className="ref">— Isaiah 40:8</span>
        </p>
        <div className="cta-group">
          <button className="btn btn-primary">ACCEPT MISSION</button>
          <button className="btn btn-secondary">PARENT LOGIN</button>
        </div>
      </header>
    </div>
  );
}

export default App;
