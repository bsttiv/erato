import type * as React from 'react';
export type Tone = 'neutral' | 'amber' | 'ember' | 'wine' | 'moss';
export type IconName = 'play' | 'pause' | 'plus' | 'x' | 'check' | 'max' | 'min' | 'left' | 'right' | 'bar' | 'guitar' | 'piano';
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'primary' | 'quiet' | 'ghost' | 'danger'; size?: 'md' | 'sm'; icon?: IconName }
export declare function Button(props: ButtonProps): React.ReactElement;
export interface TagProps { tone?: Tone; dot?: boolean; children?: React.ReactNode }
export declare function Tag(props: TagProps): React.ReactElement;
export interface SegmentedProps { options: { value: string; label: React.ReactNode }[]; value: string; onChange?: (value: string) => void; label?: string }
export declare function Segmented(props: SegmentedProps): React.ReactElement;
export interface SideNavProps { brand?: string; subtitle?: string; heading?: string; items: { id: string; label: string; meta?: string }[]; activeId?: string; defaultActiveId?: string; onSelect?: (id: string) => void }
export declare function SideNav(props: SideNavProps): React.ReactElement;
export interface ChordValue { instrument: 'guitar' | 'piano'; frets: number[]; notes: number[]; name: string | null }
export interface ChordEditorProps { defaultFrets?: number[]; defaultBaseFret?: number; defaultInstrument?: 'guitar' | 'piano'; defaultNotes?: number[]; editable?: boolean; hideSwitch?: boolean; onChange?: (value: ChordValue) => void; className?: string }
export declare function ChordEditor(props: ChordEditorProps): React.ReactElement;
export type TabColumn = string[] | '|';
export interface TabEditorProps { defaultValue?: TabColumn[]; columns?: number; strings?: string[]; title?: string; hideHint?: boolean; onChange?: (columns: TabColumn[]) => void; className?: string }
export declare function TabEditor(props: TabEditorProps): React.ReactElement;
export interface LyricsViewerProps { lyrics: string; title?: string; defaultSpeed?: number; height?: number; showChords?: boolean; className?: string }
export declare function LyricsViewer(props: LyricsViewerProps): React.ReactElement;
export interface DemoComment { t: number; author: string; text: string }
export interface DemoTake { id: string; title: string; date?: string; note?: string; duration: number; src?: string; comments?: DemoComment[] }
export interface DemoPlayerProps { takes: DemoTake[]; defaultTakeId?: string; author?: string; onComment?: (takeId: string, comment: DemoComment) => void; className?: string }
export declare function DemoPlayer(props: DemoPlayerProps): React.ReactElement;
export interface TodoItem { id: string; text: string; done: boolean }
export interface TodoListProps { defaultItems?: TodoItem[]; title?: string; placeholder?: string; onChange?: (items: TodoItem[]) => void; className?: string }
export declare function TodoList(props: TodoListProps): React.ReactElement;
export interface ChordInfo { name: string | null; root: number; quality: string | null; bass: number; notes: string[] }
export declare function detectChord(midiNotes: number[]): ChordInfo | null;
export declare function tabToText(columns: TabColumn[], stringNames?: string[]): string;
declare global { interface Window { Erato: { Button: typeof Button; Tag: typeof Tag; Segmented: typeof Segmented; SideNav: typeof SideNav; ChordEditor: typeof ChordEditor; TabEditor: typeof TabEditor; LyricsViewer: typeof LyricsViewer; DemoPlayer: typeof DemoPlayer; TodoList: typeof TodoList; detectChord: typeof detectChord; tabToText: typeof tabToText } } }
