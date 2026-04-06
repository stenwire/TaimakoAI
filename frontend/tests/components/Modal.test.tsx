import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Modal from "@/components/ui/Modal";

describe("Modal", () => {
  it("renders children when isOpen=true", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        Modal content
      </Modal>
    );
    expect(screen.getByText("Modal content")).toBeInTheDocument();
  });

  it("does not render children when isOpen=false", () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()}>
        Hidden content
      </Modal>
    );
    expect(screen.queryByText("Hidden content")).not.toBeInTheDocument();
  });

  it("renders title when provided", () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="My Modal">
        Content
      </Modal>
    );
    expect(screen.getByText("My Modal")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} title="Closable">
        Content
      </Modal>
    );
    // The close button contains an X icon; find the button in the header
    const closeButton = screen.getByRole("button");
    await user.click(closeButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when backdrop clicked", async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    const { container } = render(
      <Modal isOpen={true} onClose={handleClose} title="Backdrop Test">
        Content
      </Modal>
    );
    // The backdrop is the first div with the fixed inset-0 class and onClick={onClose}
    const backdrop = container.querySelector(".backdrop-blur-modal");
    expect(backdrop).toBeInTheDocument();
    await user.click(backdrop!);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
