export type UserRole = 'customer' | 'support_agent' | 'manager';

export interface MockSession {
  sessionId: string;
  userId: string;
  name: string;
  role: UserRole;
  accountId: string | null;
  accountName?: string;
  avatar: string;
}

export const MOCK_SESSIONS: MockSession[] = [
  {
    sessionId: 'cust-northstar',
    userId: 'user-northstar',
    name: 'Northstar Logistics',
    role: 'customer',
    accountId: 'ACCT-001',
    accountName: 'Northstar Enterprise',
    avatar: 'N',
  },
  {
    sessionId: 'cust-lumenworks',
    userId: 'user-lumenworks',
    name: 'LumenWorks Support',
    role: 'customer',
    accountId: 'ACCT-002',
    accountName: 'LumenWorks Growth',
    avatar: 'L',
  },
  {
    sessionId: 'cust-beacon',
    userId: 'user-beacon',
    name: 'Beacon Retail',
    role: 'customer',
    accountId: 'ACCT-003',
    accountName: 'Beacon Standard',
    avatar: 'B',
  },
  {
    sessionId: 'cust-axislabs',
    userId: 'user-axislabs',
    name: 'Axis Labs',
    role: 'customer',
    accountId: 'ACCT-004',
    accountName: 'Axis Standard',
    avatar: 'A',
  },
  {
    sessionId: 'agent-rohit',
    userId: 'user-rohit',
    name: 'Rohit Sharma (Tier 2 Agent)',
    role: 'support_agent',
    accountId: null,
    accountName: 'Internal Support Ops',
    avatar: 'R',
  },
  {
    sessionId: 'agent-maya',
    userId: 'user-maya',
    name: 'Maya Patel (Ops Specialist)',
    role: 'support_agent',
    accountId: null,
    accountName: 'Internal Support Ops',
    avatar: 'M',
  },
  {
    sessionId: 'manager-priya',
    userId: 'user-priya',
    name: 'Priya Mehta (Support Director)',
    role: 'manager',
    accountId: null,
    accountName: 'Operations Executive',
    avatar: 'P',
  },
];
