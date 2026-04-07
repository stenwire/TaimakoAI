import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createRef } from "react";
import Button from "@/components/ui/Button";

describe("Button", () => {
  it("renders children text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("renders with primary variant by default", () => {
    render(<Button>Primary</Button>);
    expect(screen.getByRole("button", { name: "Primary" })).toBeInTheDocument();
  });

  it("renders with secondary variant", () => {
    render(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button", { name: "Secondary" })).toBeInTheDocument();
  });

  it("renders with ghost variant", () => {
    render(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole("button", { name: "Ghost" })).toBeInTheDocument();
  });

  it("shows loading spinner when loading=true", () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole("button", { name: "Loading" });
    expect(button).toBeInTheDocument();
    // The spinner is a div with animate-spin class inside the button
    const spinner = button.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("is disabled when disabled=true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button", { name: "Disabled" })).toBeDisabled();
  });

  it("is disabled when loading=true", () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole("button", { name: "Loading" })).toBeDisabled();
  });

  it("renders as span when as='span'", () => {
    render(<Button as="span">Span Button</Button>);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    const span = screen.getByText("Span Button");
    expect(span.tagName).toBe("SPAN");
  });

  it("renders as div when as='div'", () => {
    render(<Button as="div">Div Button</Button>);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    const div = screen.getByText("Div Button");
    expect(div.tagName).toBe("DIV");
  });

  it("fires onClick handler", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Clickable</Button>);
    await user.click(screen.getByRole("button", { name: "Clickable" }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("forwards ref", () => {
    const ref = createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Ref Button</Button>);
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    expect(ref.current?.textContent).toContain("Ref Button");
  });
});
