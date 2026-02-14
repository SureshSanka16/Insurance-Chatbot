import { User } from '../types';

// Initial state is null to trigger login
export const CURRENT_USER: User = {
  id: 'u1',
  name: 'Guest',
  email: 'guest@vantage.ai',
  role: null,
  avatar: 'https://picsum.photos/seed/alex/100/100'
};

export const MOCK_USERS: User[] = [
  { id: 'u1', name: 'Alex Chen', email: 'alex.chen@vantage.ai', role: 'Admin', avatar: 'https://picsum.photos/seed/alex/100/100' },
  { id: 'u5', name: 'James Doe', email: 'james.doe@gmail.com', role: 'User', avatar: 'https://picsum.photos/seed/james/100/100' },
  { id: 'u2', name: 'Sarah Connor', email: 'sarah.connor@vantage.ai', role: 'Admin', avatar: 'https://picsum.photos/seed/sarah/100/100' },
  { id: 'u3', name: 'John Wick', email: 'john.wick@vantage.ai', role: 'Admin', avatar: 'https://picsum.photos/seed/john/100/100' },
];