import { Layout } from '../components/layout/Layout';
import { LoginForm } from '../components/auth/LoginForm';

export function LoginPage() {
  return (
    <Layout showHeader={false} className="p-0">
      <LoginForm />
    </Layout>
  );
}
