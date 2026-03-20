
export interface AppEntry {
    label: string;
    url: string;
    port?: number;
    whatItIs: string;
    whatYouCanDo: string;
}

export const APPS_CATALOG: AppEntry[] = [
    {
        label: "Git GitHub MCP",
        url: "http://127.0.0.1:10702",
        port: 10702,
        whatItIs: "This app. Manage your Git repositories and GitHub interactions.",
        whatYouCanDo: "View repositories, commit history, and chat with your codebase.",
    },
    {
        label: "Advanced Memory",
        url: "http://127.0.0.1:10704",
        port: 10704,
        whatItIs: "A knowledge base that stores notes, research, and links in a graph.",
        whatYouCanDo: "Add and search notes, build context for AI conversations.",
    },
    {
        label: "Robotics MCP",
        url: "http://127.0.0.1:10706",
        port: 10706,
        whatItIs: "Tools for robots and automation control.",
        whatYouCanDo: "Monitor and control robots.",
    },
    {
        label: "Calibre MCP",
        url: "http://127.0.0.1:10721",
        port: 10721,
        whatItIs: "Manage your e-book library.",
        whatYouCanDo: "Search books, metadata, and read.",
    },
    {
        label: "WinRAR MCP",
        url: "http://127.0.0.1:10763",
        port: 10763,
        whatItIs: "Manage archives and compression.",
        whatYouCanDo: "Create and extract archives.",
    },
    {
        label: "MyAI Dashboard",
        url: "http://127.0.0.1:3060",
        port: 3060,
        whatItIs: "Central dashboard for MyAI microservices.",
        whatYouCanDo: "Manage services and view status.",
    },
];
