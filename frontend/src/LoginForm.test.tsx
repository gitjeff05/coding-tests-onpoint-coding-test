import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginForm from "./LoginForm";
import * as api from "./api";
import * as auth from "./auth";

vi.mock("./api");
vi.mock("./auth");

const mockedApi = vi.mocked(api);
const mockedAuth = vi.mocked(auth);

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders username and password fields", () => {
    render(<LoginForm onLoggedIn={vi.fn()} />);
    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
  });

  it("logs in with valid credentials", async () => {
    mockedApi.login.mockResolvedValue({ access_token: "jwt-token", token_type: "bearer" });
    const onLoggedIn = vi.fn();

    render(<LoginForm onLoggedIn={onLoggedIn} />);
    fireEvent.change(screen.getByPlaceholderText("Username"), { target: { value: "admin" } });
    fireEvent.change(screen.getByPlaceholderText("Password"), { target: { value: "admin123" } });
    fireEvent.click(screen.getByText("Log in"));

    await waitFor(() => {
      expect(mockedApi.login).toHaveBeenCalledWith("admin", "admin123");
      expect(mockedAuth.setToken).toHaveBeenCalledWith("jwt-token");
      expect(onLoggedIn).toHaveBeenCalled();
    });
  });

  it("shows an error and does not log in on invalid credentials", async () => {
    mockedApi.login.mockRejectedValue(new Error("invalid username or password"));
    const onLoggedIn = vi.fn();

    render(<LoginForm onLoggedIn={onLoggedIn} />);
    fireEvent.change(screen.getByPlaceholderText("Username"), { target: { value: "admin" } });
    fireEvent.change(screen.getByPlaceholderText("Password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByText("Log in"));

    expect(await screen.findByText("invalid username or password")).toBeInTheDocument();
    expect(onLoggedIn).not.toHaveBeenCalled();
  });
});
