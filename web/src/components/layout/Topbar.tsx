'use client';

import { APPS_CATALOG } from '@/common/apps-catalog';
import { LayoutGrid, ExternalLink, HelpCircle, Activity } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

export function Topbar() {
    return (
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-950 px-6 shadow-sm">
            <div className="flex items-center gap-4">
                {/* Left side content (breadcrumbs etc) could go here */}
            </div>

            <div className="flex items-center gap-4">
                {/* Apps Dropdown */}
                <DropdownMenu.Root>
                    <DropdownMenu.Trigger asChild>
                        <button className="flex items-center gap-2 rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors outline-none focus:ring-2 focus:ring-slate-700">
                            <LayoutGrid className="h-5 w-5" />
                            <span className="hidden sm:inline-block text-sm font-medium">Apps</span>
                        </button>
                    </DropdownMenu.Trigger>

                    <DropdownMenu.Portal>
                        <DropdownMenu.Content
                            className="z-50 w-80 rounded-md border border-slate-800 bg-slate-950 p-2 shadow-xl animate-in fade-in zoom-in-95 duration-200"
                            align="end"
                            sideOffset={5}
                        >
                            <div className="px-2 py-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Our Apps
                            </div>
                            <div className="h-px bg-slate-800 my-1" />
                            <div className="max-h-[60vh] overflow-y-auto space-y-1">
                                {APPS_CATALOG.map((app) => (
                                    <DropdownMenu.Item key={app.url} asChild>
                                        <a
                                            href={app.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-start gap-3 rounded-md p-2 outline-none hover:bg-slate-800 focus:bg-slate-800 group"
                                        >
                                            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded bg-slate-900 text-slate-400 group-hover:bg-slate-700 group-hover:text-blue-400 transition-colors">
                                                <ExternalLink className="h-4 w-4" />
                                            </div>
                                            <div className="flex-1 space-y-1">
                                                <p className="text-sm font-medium text-slate-200 group-hover:text-blue-300">
                                                    {app.label}
                                                </p>
                                                <p className="text-xs text-slate-500 line-clamp-2">
                                                    {app.whatItIs}
                                                </p>
                                            </div>
                                        </a>
                                    </DropdownMenu.Item>
                                ))}
                            </div>
                        </DropdownMenu.Content>
                    </DropdownMenu.Portal>
                </DropdownMenu.Root>

                <div className="h-6 w-px bg-slate-800" />

                <button className="text-slate-400 hover:text-slate-100 transition-colors" title="System Status">
                    <Activity className="h-5 w-5" />
                </button>
                <button className="text-slate-400 hover:text-slate-100 transition-colors" title="Help">
                    <HelpCircle className="h-5 w-5" />
                </button>
            </div>
        </header>
    );
}
