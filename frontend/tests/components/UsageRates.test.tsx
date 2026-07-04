import { render, screen } from "@testing-library/react";
import UsageRates from "@/components/dashboard/subscription/UsageRates";

const defaultProps = {
  tier: "spark",
  allocatedAiResponses: 1000,
  usedAiResponses: 200,
  allocatedEscalations: 50,
  usedEscalations: 10,
  planFeatures: null,
};

describe("UsageRates", () => {
  it("shows 'Unlimited' when allocatedAiResponses > 99999", () => {
    render(<UsageRates {...defaultProps} allocatedAiResponses={100000} />);
    expect(screen.getByText("Unlimited")).toBeInTheDocument();
  });

  it("shows 'Unlimited' when allocatedAiResponses === -1", () => {
    render(<UsageRates {...defaultProps} allocatedAiResponses={-1} />);
    expect(screen.getByText("Unlimited")).toBeInTheDocument();
  });

  it("shows 'X / Y' format for normal allocations", () => {
    render(<UsageRates {...defaultProps} allocatedAiResponses={1000} usedAiResponses={200} />);
    expect(screen.getByText("200 / 1,000")).toBeInTheDocument();
  });

  it("shows low credit warning when usage > 85%", () => {
    render(
      <UsageRates
        {...defaultProps}
        allocatedAiResponses={100}
        usedAiResponses={90}
      />
    );
    expect(screen.getByText(/Running low on credits/)).toBeInTheDocument();
  });

  it("does not show low credit warning when usage <= 85%", () => {
    render(
      <UsageRates
        {...defaultProps}
        allocatedAiResponses={100}
        usedAiResponses={50}
      />
    );
    expect(screen.queryByText(/Running low on credits/)).not.toBeInTheDocument();
  });

  it("shows 'N/A' for escalations when maxEscalations === 0", () => {
    render(<UsageRates {...defaultProps} allocatedEscalations={0} />);
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("shows upgrade message when maxEscalations === 0", () => {
    render(<UsageRates {...defaultProps} allocatedEscalations={0} />);
    expect(screen.getByText("Upgrade plan to unlock Human Handoff")).toBeInTheDocument();
  });

  it("shows 'Team escalations included' when maxEscalations > 0", () => {
    render(<UsageRates {...defaultProps} allocatedEscalations={50} />);
    expect(screen.getByText("Team escalations included")).toBeInTheDocument();
  });
});
