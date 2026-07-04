import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Card from "@/components/ui/Card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders title when provided", () => {
    render(<Card title="Card Title">Content</Card>);
    expect(screen.getByText("Card Title")).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<Card subtitle="Card Subtitle">Content</Card>);
    expect(screen.getByText("Card Subtitle")).toBeInTheDocument();
  });

  it("renders headerAction slot", () => {
    render(
      <Card headerAction={<button>Action</button>}>Content</Card>
    );
    expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
  });

  it("shows no header when no title/subtitle/headerAction", () => {
    const { container } = render(<Card>Just content</Card>);
    const header = container.querySelector(".attio-card-header");
    expect(header).not.toBeInTheDocument();
  });

  it("fires onClick handler", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Card onClick={handleClick}>Clickable card</Card>);
    await user.click(screen.getByText("Clickable card"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
