import { render, screen } from "@testing-library/react";
import { createRef } from "react";
import Input from "@/components/ui/Input";

describe("Input", () => {
  it("renders without label", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
    expect(screen.queryByText(/./)).toBeNull(); // no label or error text
  });

  it("renders with label text", () => {
    render(<Input label="Email" />);
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("shows error message when error prop provided", () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText("This field is required")).toBeInTheDocument();
  });

  it("forwards ref", () => {
    const ref = createRef<HTMLInputElement>();
    render(<Input ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it("passes through placeholder attribute", () => {
    render(<Input placeholder="Type here..." />);
    expect(screen.getByPlaceholderText("Type here...")).toBeInTheDocument();
  });

  it("passes through type attribute", () => {
    render(<Input type="password" placeholder="pwd" />);
    const input = screen.getByPlaceholderText("pwd");
    expect(input).toHaveAttribute("type", "password");
  });

  it("passes through other HTML input attributes", () => {
    render(<Input name="username" autoComplete="off" placeholder="user" />);
    const input = screen.getByPlaceholderText("user");
    expect(input).toHaveAttribute("name", "username");
    expect(input).toHaveAttribute("autoComplete", "off");
  });
});
