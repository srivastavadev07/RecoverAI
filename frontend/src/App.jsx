import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import api from "./api";

/* =========================================================
   METRIC CARD
========================================================= */

function MetricCard({ title, value, subtitle }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <p className="text-sm text-slate-400">{title}</p>

      <p className="mt-2 text-3xl font-bold text-white">{value}</p>

      {subtitle && <p className="mt-2 text-xs text-slate-500">{subtitle}</p>}
    </div>
  );
}

/* =========================================================
   MAIN APP
========================================================= */

function App() {
  /* -------------------------------------------------------
     DASHBOARD STATE
  ------------------------------------------------------- */

  const [summary, setSummary] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [evaluation, setEvaluation] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /* -------------------------------------------------------
     AI ANALYSIS STATE
  ------------------------------------------------------- */

  const [selectedPayment, setSelectedPayment] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);

  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

  /* -------------------------------------------------------
     EXECUTION STATE
  ------------------------------------------------------- */

  const [executionLoading, setExecutionLoading] = useState(false);

  const [executionResult, setExecutionResult] = useState(null);

  const [executionError, setExecutionError] = useState(null);

  /* =======================================================
     LOAD DASHBOARD DATA
  ======================================================= */

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryResponse, opportunitiesResponse, evaluationResponse] =
          await Promise.all([
            api.get("/analytics/recovery-summary"),

            api.get("/recovery/opportunities"),

            api.get("/evaluation/recovery"),
          ]);

        /* -----------------------------------------------
           Store API data
        ----------------------------------------------- */

        setSummary(summaryResponse.data);

        setOpportunities(opportunitiesResponse.data.opportunities || []);

        // IMPORTANT:
        // Store evaluation API response.
        setEvaluation(evaluationResponse.data);
      } catch (err) {
        console.error("Dashboard loading error:", err);

        setError("Unable to load RecoverAI dashboard data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  /* =======================================================
     ANALYZE PAYMENT WITH AI
  ======================================================= */

  async function analyzePayment(opportunity) {
    setSelectedPayment(opportunity);

    // Clear previous AI state
    setAiAnalysis(null);
    setAiError(null);

    // Clear previous execution state
    setExecutionResult(null);
    setExecutionError(null);

    setAiLoading(true);

    try {
      const response = await api.get(
        `/recovery/analyze/${opportunity.payment_id}`,
      );

      setAiAnalysis(response.data);
    } catch (err) {
      console.error("AI analysis error:", err);

      setAiError("Unable to get AI analysis.");
    } finally {
      setAiLoading(false);
    }
  }

  /* =======================================================
     EXECUTE RECOVERY
  ======================================================= */

  async function executeRecovery() {
    // Safety check
    if (!selectedPayment) {
      return;
    }

    if (!aiAnalysis) {
      return;
    }

    const action = aiAnalysis.decision;

    // Only allow known actions
    const allowedActions = [
      "retry_payment",
      "create_payment_link",
      "send_notification",
    ];

    if (!allowedActions.includes(action)) {
      setExecutionError("Invalid recovery action selected by AI.");

      return;
    }

    setExecutionLoading(true);

    setExecutionResult(null);
    setExecutionError(null);

    try {
      const response = await api.post(
        `/recovery/execute/${selectedPayment.payment_id}`,
        {
          action: action,
        },
      );

      setExecutionResult(response.data);
    } catch (err) {
      console.error("Recovery execution error:", err);

      setExecutionError("Unable to execute recovery action.");
    } finally {
      setExecutionLoading(false);
    }
  }

  /* =======================================================
     LOADING SCREEN
  ======================================================= */

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-slate-700 border-t-white" />

          <p className="text-slate-400">Loading RecoverAI...</p>
        </div>
      </div>
    );
  }

  /* =======================================================
     ERROR SCREEN
  ======================================================= */

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 p-10 text-white">
        <div className="mx-auto max-w-3xl rounded-2xl border border-red-900 bg-red-950/30 p-6">
          <h2 className="text-lg font-semibold text-red-400">
            Dashboard Error
          </h2>

          <p className="mt-2 text-sm text-red-300">{error}</p>
        </div>
      </div>
    );
  }

  /* =======================================================
     SAFE VALUES
  ======================================================= */

  const revenueAtRisk = summary?.revenue_at_risk ?? 0;

  const expectedRecovery = summary?.expected_recovery ?? 0;

  const failedPayments = summary?.failed_payments ?? 0;

  const urgentOpportunities = summary?.urgent_opportunities ?? 0;

  const revenueRecovered = evaluation?.revenue_recovered ?? 0;

  const recoveryAttempts = evaluation?.recovery_attempts ?? 0;

  const successfulRecoveries = evaluation?.successful_recoveries ?? 0;

  const blockedActions = evaluation?.blocked_actions ?? 0;

  const recoveryRate = (evaluation?.recovery_rate ?? 0) * 100;

  /* =======================================================
     CHART DATA
  ======================================================= */

  const recoveryChartData = [
    {
      name: "At Risk",
      amount: revenueAtRisk,
    },

    {
      name: "Expected",
      amount: expectedRecovery,
    },

    {
      name: "Recovered",
      amount: revenueRecovered,
    },
  ];

  /* =======================================================
     ACTION DATA
  ======================================================= */

  const actionCounts = evaluation?.action_counts ?? {};

  /* =======================================================
     DASHBOARD
  ======================================================= */

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* =================================================
          HEADER
      ================================================= */}

      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-2xl font-bold">RecoverAI</h1>

            <p className="mt-1 text-sm text-slate-400">
              AI Revenue Recovery Command Center
            </p>
          </div>

          {/* Agent status */}

          <div className="flex items-center gap-2 rounded-full border border-emerald-900 bg-emerald-950/40 px-4 py-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />

            <span className="text-sm text-emerald-400">Agent Operational</span>
          </div>
        </div>
      </header>

      {/* =================================================
          MAIN CONTENT
      ================================================= */}

      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* =================================================
            REVENUE OVERVIEW
        ================================================= */}

        <section>
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Revenue Overview</h2>

            <p className="mt-1 text-sm text-slate-500">
              Recovery intelligence from current payment data
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard
              title="Revenue at Risk"
              value={`₹${revenueAtRisk.toLocaleString("en-IN")}`}
              subtitle={`${failedPayments} failed payments`}
            />

            <MetricCard
              title="Expected Recovery"
              value={`₹${expectedRecovery.toLocaleString("en-IN")}`}
              subtitle="Estimated recoverable value"
            />

            <MetricCard
              title="Urgent Opportunities"
              value={urgentOpportunities}
              subtitle="Require immediate attention"
            />

            <MetricCard
              title="Recovery Opportunities"
              value={opportunities.length}
              subtitle="Detected failed payments"
            />

            <MetricCard
              title="Revenue Recovered"
              value={`₹${revenueRecovered.toLocaleString("en-IN")}`}
              subtitle="Recovered in simulation"
            />

            <MetricCard
              title="Recovery Attempts"
              value={recoveryAttempts}
              subtitle="Actions attempted"
            />

            <MetricCard
              title="Successful Recoveries"
              value={successfulRecoveries}
              subtitle="Successful outcomes"
            />

            <MetricCard
              title="Recovery Rate"
              value={`${recoveryRate.toFixed(1)}%`}
              subtitle="Synthetic evaluation"
            />
          </div>
        </section>

        {/* =================================================
            RECOVERY PERFORMANCE CHART
        ================================================= */}

        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Recovery Performance</h2>

            <p className="mt-1 text-sm text-slate-500">
              Revenue exposure compared with expected and simulated recovery
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <div className="h-[320px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={recoveryChartData}
                  margin={{
                    top: 20,
                    right: 20,
                    left: 20,
                    bottom: 20,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

                  <XAxis
                    dataKey="name"
                    tick={{
                      fill: "#94a3b8",
                    }}
                    axisLine={{
                      stroke: "#334155",
                    }}
                  />

                  <YAxis
                    tick={{
                      fill: "#94a3b8",
                    }}
                    axisLine={{
                      stroke: "#334155",
                    }}
                    tickFormatter={(value) =>
                      `₹${(Number(value) / 100000).toFixed(1)}L`
                    }
                  />

                  <Tooltip
                    formatter={(value) =>
                      `₹${Number(value).toLocaleString("en-IN")}`
                    }
                  />

                  <Bar dataKey="amount" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* =================================================
            RECOVERY STRATEGY
        ================================================= */}

        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Recovery Strategy</h2>

            <p className="mt-1 text-sm text-slate-500">
              How RecoverAI distributes recovery actions
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {Object.entries(actionCounts).length === 0 ? (
              <div className="col-span-full rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center">
                <p className="text-sm text-slate-500">
                  No recovery strategy data available.
                </p>
              </div>
            ) : (
              Object.entries(actionCounts).map(([action, count]) => (
                <div
                  key={action}
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                >
                  <p className="text-sm text-slate-400">{action}</p>

                  <p className="mt-2 text-3xl font-bold">{count}</p>

                  <p className="mt-2 text-xs text-slate-500">
                    Recovery decisions
                  </p>
                </div>
              ))
            )}
          </div>
        </section>

        {/* =================================================
            RECOVERY QUEUE
        ================================================= */}

        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">Recovery Opportunities</h2>

            <p className="mt-1 text-sm text-slate-500">
              Click a payment to ask RecoverAI for a recovery decision
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left">
                {/* TABLE HEADER */}

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

                {/* TABLE BODY */}

                <tbody>
                  {opportunities.length === 0 ? (
                    <tr>
                      <td
                        colSpan="6"
                        className="px-5 py-10 text-center text-slate-500"
                      >
                        No recovery opportunities found.
                      </td>
                    </tr>
                  ) : (
                    opportunities.slice(0, 10).map((opportunity) => (
                      <tr
                        key={opportunity.payment_id}
                        onClick={() => analyzePayment(opportunity)}
                        className="cursor-pointer border-b border-slate-800 transition last:border-0 hover:bg-slate-800/60"
                      >
                        {/* PRIORITY */}

                        <td className="px-5 py-4">
                          <span
                            className={`rounded-full border px-3 py-1 text-xs ${
                              opportunity.opportunity_priority === "URGENT"
                                ? "border-red-800 bg-red-950/40 text-red-400"
                                : opportunity.opportunity_priority === "HIGH"
                                  ? "border-amber-800 bg-amber-950/40 text-amber-400"
                                  : "border-slate-700 text-slate-300"
                            }`}
                          >
                            {opportunity.opportunity_priority}
                          </span>
                        </td>

                        {/* CUSTOMER */}

                        <td className="px-5 py-4">
                          <div className="font-medium text-white">
                            {opportunity.customer_id}
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            Payment #{opportunity.payment_id}
                          </div>
                        </td>

                        {/* AMOUNT */}

                        <td className="px-5 py-4 font-medium">
                          ₹{opportunity.amount.toLocaleString("en-IN")}
                        </td>

                        {/* RISK */}

                        <td className="px-5 py-4">
                          <span className="font-medium">
                            {opportunity.risk_score}
                          </span>

                          <span className="text-slate-500">/100</span>
                        </td>

                        {/* EXPECTED RECOVERY */}

                        <td className="px-5 py-4">
                          ₹
                          {opportunity.expected_recovery.toLocaleString(
                            "en-IN",
                          )}
                        </td>

                        {/* ACTION */}

                        <td className="px-5 py-4 text-sm text-slate-300">
                          {opportunity.recommended_action}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* =================================================
            AI RECOVERY CENTER
        ================================================= */}

        <section className="mt-10">
          <div className="mb-5">
            <h2 className="text-xl font-semibold">AI Recovery Center</h2>

            <p className="mt-1 text-sm text-slate-500">
              AI recommendation → merchant approval → guarded execution
            </p>
          </div>

          {/* ------------------------------------------------
              NOTHING SELECTED
          ------------------------------------------------ */}

          {!selectedPayment && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center">
              <div className="text-4xl">🤖</div>

              <p className="mt-4 text-slate-300">
                Select a recovery opportunity above
              </p>

              <p className="mt-2 text-sm text-slate-500">
                RecoverAI will analyze the payment and recommend the safest
                recovery action.
              </p>
            </div>
          )}

          {/* ------------------------------------------------
              SELECTED PAYMENT
          ------------------------------------------------ */}

          {selectedPayment && (
            <div className="grid gap-6 lg:grid-cols-2">
              {/* ==========================================
                  PAYMENT DETAILS
              ========================================== */}

              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  Selected Payment
                </p>

                <h3 className="mt-2 text-2xl font-bold">
                  Payment #{selectedPayment.payment_id}
                </h3>

                <div className="mt-6 space-y-4">
                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">Customer</span>

                    <span className="text-sm font-medium">
                      {selectedPayment.customer_id}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">Amount</span>

                    <span className="text-sm font-semibold">
                      ₹{selectedPayment.amount.toLocaleString("en-IN")}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">
                      Failure Reason
                    </span>

                    <span className="text-sm text-slate-300">
                      {selectedPayment.failure_reason}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">
                      Payment Method
                    </span>

                    <span className="text-sm text-slate-300">
                      {selectedPayment.payment_method}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">Retry Count</span>

                    <span className="text-sm text-slate-300">
                      {selectedPayment.retry_count}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">Risk Score</span>

                    <span className="text-sm font-medium">
                      {selectedPayment.risk_score}
                      /100
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">
                      Recovery Probability
                    </span>

                    <span className="text-sm font-medium">
                      {(selectedPayment.recovery_probability * 100).toFixed(1)}%
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-5">
                    <span className="text-sm text-slate-400">
                      Expected Recovery
                    </span>

                    <span className="text-sm font-semibold">
                      ₹
                      {selectedPayment.expected_recovery.toLocaleString(
                        "en-IN",
                      )}
                    </span>
                  </div>
                </div>
              </div>

              {/* ==========================================
                  AI DECISION
              ========================================== */}

              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-xs uppercase tracking-wider text-slate-500">
                  RecoverAI Decision
                </p>

                {/* AI LOADING */}

                {aiLoading && (
                  <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950 p-6 text-center">
                    <div className="mx-auto mb-4 h-7 w-7 animate-spin rounded-full border-2 border-slate-700 border-t-white" />

                    <p className="text-sm text-slate-400">
                      🤖 RecoverAI is analyzing the opportunity...
                    </p>
                  </div>
                )}

                {/* AI ERROR */}

                {aiError && (
                  <div className="mt-6 rounded-xl border border-red-900 bg-red-950/30 p-5">
                    <p className="text-sm text-red-400">❌ {aiError}</p>
                  </div>
                )}

                {/* AI ANALYSIS */}

                {aiAnalysis && (
                  <div className="mt-6 space-y-5">
                    <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">
                      <p className="text-xs uppercase tracking-wider text-slate-500">
                        Recommended Action
                      </p>

                      <p className="mt-2 text-2xl font-bold text-white">
                        {aiAnalysis.decision}
                      </p>

                      <div className="mt-4">
                        <span className="rounded-full border border-amber-800 bg-amber-950/40 px-3 py-1 text-xs text-amber-400">
                          Awaiting Merchant Approval
                        </span>
                      </div>

                      {aiAnalysis.arguments && (
                        <div className="mt-5">
                          <p className="text-xs uppercase tracking-wider text-slate-500">
                            AI Parameters
                          </p>

                          <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-400">
                            {JSON.stringify(aiAnalysis.arguments, null, 2)}
                          </pre>
                        </div>
                      )}

                      <button
                        onClick={executeRecovery}
                        disabled={
                          executionLoading ||
                          aiAnalysis.status !== "AWAITING_APPROVAL"
                        }
                        className="mt-6 w-full rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {executionLoading
                          ? "Executing Recovery..."
                          : "Execute Recovery"}
                      </button>
                    </div>

                    {/* EXECUTION RESULT */}

                    {executionResult && (
                      <div
                        className={`rounded-xl border p-5 ${
                          executionResult.success
                            ? "border-emerald-900 bg-emerald-950/30"
                            : "border-red-900 bg-red-950/30"
                        }`}
                      >
                        {executionResult.success ? (
                          <>
                            <p className="text-sm font-semibold text-emerald-400">
                              ✅ Recovery action executed
                            </p>

                            <div className="mt-4 space-y-2 text-sm">
                              <p className="text-slate-300">
                                Action:
                                <span className="ml-2 font-medium text-white">
                                  {executionResult.action}
                                </span>
                              </p>

                              <p className="text-slate-300">
                                Status:
                                <span className="ml-2 font-medium text-emerald-400">
                                  {executionResult.audit_status}
                                </span>
                              </p>
                            </div>

                            {/* Razorpay Payment Link */}

                            {executionResult.tool_result?.payment_link && (
                              <a
                                href={executionResult.tool_result.payment_link}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-4 inline-block rounded-lg border border-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-800"
                              >
                                Open Razorpay Payment Link →
                              </a>
                            )}
                          </>
                        ) : (
                          <>
                            <p className="text-sm font-semibold text-red-400">
                              🛑 Recovery action blocked
                            </p>

                            <p className="mt-3 text-sm text-slate-300">
                              {executionResult.tool_result?.reason ||
                                "The recovery action was not executed."}
                            </p>
                          </>
                        )}
                      </div>
                    )}

                    {/* EXECUTION ERROR */}

                    {executionError && (
                      <div className="rounded-xl border border-red-900 bg-red-950/30 p-5">
                        <p className="text-sm text-red-400">
                          ❌ {executionError}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </main>

      {/* =================================================
          FOOTER
      ================================================= */}

      <footer className="border-t border-slate-800">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <p className="text-center text-xs text-slate-600">
            RecoverAI • AI-powered revenue recovery platform
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
