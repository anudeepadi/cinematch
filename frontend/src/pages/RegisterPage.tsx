import { Layout } from '../components/layout/Layout';
import { RegisterForm } from '../components/auth/RegisterForm';

export function RegisterPage() {
  return (
    <Layout showHeader={false} className="p-0">
      <RegisterForm />
    </Layout>
  );
}
