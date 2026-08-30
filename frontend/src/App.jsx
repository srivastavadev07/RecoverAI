import { useEffect, useState } from "react";
import api from "./api";

function MetricCard({ title, value, subtitle }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <p className="text-sm text-slate-400">{title}</p>

      <p className="mt-2 text-3xl font-bold text-white">{value}</p>

      {subtitle && <p className="mt-2 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}

function App() {
  const [summary, setSummary] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedPayment, setSelectedPayment] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

  async function analyzePayment(opportunity) {
    setSelectedPayment(opportunity);
    setAiAnalysis(null);
    setAiError(null);
    setAiLoading(true);

    try {
      const response = await api.get(
        `/recovery/analyze/${opportunity.payment_id}`,
      );

      setAiAnalysis(response.data);
    } catch (err) {
      console.error(err);

      setAiError("Unable to get AI analysis.");
    } finally {
      setAiLoading(false);
    }
  }

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryResponse, opportunitiesResponse] = await Promise.all([
          api.get("/analytics/recovery-summary"),
          api.get("/recovery/opportunities"),
        ]);

        setSummary(summaryResponse.data);
        setOpportunities(opportunitiesResponse.data.opportunities);
      } catch (err) {
        console.error(err);
        setError("Unable to load RecoverAI dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <p className="text-slate-400">Loading RecoverAI...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white p-10">
        <div className="rounded-2xl border border-red-900 bg-red-950/30 p-6">
          <p className="text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  const revenueAtRisk = summary?.revenue_at_risk ?? 0;

  const expectedRecovery = summary?.expected_recovery ?? 0;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="mx-auto max-w-7xl px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">RecoverAI</h1>

            <p className="text-sm text-slate-400">
              AI Revenue Recovery Command Center
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-emerald-900 bg-emerald-950/40 px-4 py-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />

            <span className="text-sm text-emerald-400">Agent Operational</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Overview */}
        <section>
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Revenue Overview</h2>

            <p className="text-sm text-slate-500">
              Real-time recovery intelligence
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard
              title="Revenue at Risk"
              value={`₹${revenueAtRisk.toLocaleString("en-IN")}`}
              subtitle={`${summary?.failed_payments ?? 0} failed payments`}
            />

            <MetricCard
              title="Expected Recovery"
              value={`₹${expectedRecovery.toLocaleString("en-IN")}`}
              subtitle="AI estimated recoverable value"
            />

            <MetricCard
              title="Urgent Opportunities"
              value={summary?.urgent_opportunities ?? 0}
              subtitle="Require immediate attention"
            />
          </div>
        </section>

        {/* Recovery Queue */}
        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Recovery Opportunities</h2>

            <p className="text-sm text-slate-500">
              Highest-value recovery opportunities first
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="border-b border-slate-800 bg-slate-950">
                  <tr>
                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Priority
                    </th>

                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Customer
                    </th>

                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Amount
                    </th>

                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Risk
                    </th>

                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Expected Recovery
                    </th>

                    <th className="px-5 py-4 text-xs font-medium text-slate-400">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {opportunities.slice(0, 10).map((opportunity) => (
                    <tr
                      key={opportunity.payment_id}
                      onClick={() => analyzePayment(opportunity)}
                      className="cursor-pointer border-b border-slate-800 last:border-0 hover:bg-slate-800/50"
                    >
                      <td className="px-5 py-4">
                        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs">
                          {opportunity.opportunity_priority}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-medium">
                          {opportunity.customer_id}
                        </div>

                        <div className="text-xs text-slate-500">
                          Payment #{opportunity.payment_id}
                        </div>
                      </td>

                      <td className="px-5 py-4 font-medium">
                        ₹{opportunity.amount.toLocaleString("en-IN")}
                      </td>

                      <td className="px-5 py-4">
                        <span className="font-medium">
                          {opportunity.risk_score}
                        </span>

                        <span className="text-slate-500">/100</span>
                      </td>

                      <td className="px-5 py-4">
                        ₹{opportunity.expected_recovery.toLocaleString("en-IN")}
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-300">
                        {opportunity.recommended_action}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

      <section className="mt-10">

  <div className="mb-5">
    <h2 className="text-xl font-semibold">
      AI Recovery Center
    </h2>

    <p className="text-sm text-slate-500">
      AI-powered recovery decision and execution
    </p>
  </div>


  {!selectedPayment && (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
      <p className="text-slate-400">
        Select a recovery opportunity above to analyze it with RecoverAI.
      </p>
    </div>
  )}


  {selectedPayment && (
    <div className="grid gap-6 lg:grid-cols-2">

      {/* Payment information */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

        <p className="text-sm text-slate-500">
          Selected Payment
        </p>

        <h3 className="mt-2 text-2xl font-bold">
          Payment #{selectedPayment.payment_id}
        </h3>

        <div className="mt-6 space-y-4">

          <div className="flex justify-between">
            <span className="text-slate-400">
              Customer
            </span>

            <span>
              {selectedPayment.customer_id}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-slate-400">
              Amount
            </span>

            <span className="font-semibold">
              ₹{selectedPayment.amount.toLocaleString("en-IN")}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-slate-400">
              Failure
            </span>

            <span>
              {selectedPayment.failure_reason}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-slate-400">
              Risk Score
            </span>

            <span>
              {selectedPayment.risk_score}/100
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-slate-400">
              Expected Recovery
            </span>

            <span>
              ₹
              {selectedPayment.expected_recovery.toLocaleString(
                "en-IN"
              )}
            </span>
          </div>

        </div>

      </div>


      {/* AI decision */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

        <p className="text-sm text-slate-500">
          RecoverAI Decision
        </p>

        {aiLoading && (
          <div className="mt-6">
            <p className="text-slate-400">
              🤖 AI is analyzing the opportunity...
            </p>
          </div>
        )}

        {aiError && (
          <div className="mt-6 rounded-xl border border-red-900 bg-red-950/30 p-4">
            <p className="text-red-400">
              {aiError}
            </p>
          </div>
        )}

        {aiAnalysis && (
          <div className="mt-6">

            <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">

              <p className="text-xs uppercase tracking-wider text-slate-500">
                AI Decision
              </p>

              <p className="mt-2 text-xl font-bold">
                {aiAnalysis.decision}
              </p>

              <div className="mt-5 space-y-4">

  <div>
    <p className="text-xs uppercase tracking-wider text-slate-500">
      Selected Action
    </p>

    <p className="mt-1 text-sm font-medium text-white">
      {aiAnalysis.decision}
    </p>
  </div>

  {aiAnalysis.arguments && (
    <div>
      <p className="text-xs uppercase tracking-wider text-slate-500">
        Arguments
      </p>

      <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-300">
        {JSON.stringify(
          aiAnalysis.arguments,
          null,
          2
        )}
      </pre>
    </div>
  )}

  {aiAnalysis.tool_result && (
    <div>
      <p className="text-xs uppercase tracking-wider text-slate-500">
        Tool Result
      </p>

      <pre className="mt-2 whitespace-pre-wrap text-sm text-slate-300">
        {JSON.stringify(
          aiAnalysis.tool_result,
          null,
          2
        )}
      </pre>
    </div>
  )}

</div>

            </div>

          </div>
        )}

      </div>

    </div>
  )}

</section>
      </main>
    </div>
  );
}

export default App;
