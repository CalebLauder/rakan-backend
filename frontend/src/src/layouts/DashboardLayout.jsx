// src/layouts/DashboardLayout.jsx
export default function DashboardLayout({ children }) {
  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h2>Rakan</h2>
        <p className="sidebar-subtitle">Smart Home Overview</p>
        {/* Later we can add filters / modes here */}
      </aside>

      <section className="dashboard-main">
        {children}
      </section>
    </div>
  );
}
