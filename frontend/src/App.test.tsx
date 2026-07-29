import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./api";
import * as auth from "./auth";
import type { TreeNode } from "./types";

vi.mock("./api");
vi.mock("./auth");

const mockedApi = vi.mocked(api);
const mockedAuth = vi.mocked(auth);

const sampleTree: TreeNode[] = [
  {
    id: 1,
    level: "location",
    name: "Perimeter",
    parent_id: null,
    children: [
      {
        id: 2,
        level: "department",
        name: "Bakery",
        parent_id: 1,
        children: [],
      },
    ],
  },
];

beforeEach(() => {
  mockedApi.getTree.mockResolvedValue(sampleTree);
  mockedAuth.getToken.mockReturnValue("fake-token");
});

describe("App", () => {
  it("renders the hierarchy tree from the API", async () => {
    render(<App />);
    expect(await screen.findByText("Perimeter")).toBeInTheDocument();
    expect(await screen.findByText("Bakery")).toBeInTheDocument();
  });

  it("shows an error message if loading the tree fails", async () => {
    mockedApi.getTree.mockRejectedValueOnce(new Error("network down"));
    render(<App />);
    expect(await screen.findByText("network down")).toBeInTheDocument();
  });

  it("creates a new location and reloads the tree", async () => {
    mockedApi.createNode.mockResolvedValue({
      id: 99,
      level: "location",
      name: "New Loc",
      parent_id: null,
    });

    render(<App />);
    await screen.findByText("Perimeter");

    fireEvent.change(screen.getByPlaceholderText("New location name"), {
      target: { value: "New Loc" },
    });
    fireEvent.click(screen.getByText("+ location"));

    await waitFor(() => {
      expect(mockedApi.createNode).toHaveBeenCalledWith({
        level: "location",
        name: "New Loc",
        parent_id: null,
      });
    });
  });
});
