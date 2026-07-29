/**
 * GBT SDK TypeScript declarations.
 *
 * @example
 *   import GBT, { GBTError } from '@gbt/sdk';
 */

declare class GBTError extends Error {
  name: 'GBTError';
  status?: number;
  body?: any;
  headers: Record<string, string>;

  constructor(message: string, status?: number, body?: any, headers?: Record<string, string>);
  toString(): string;
}

interface GBTCheckoutPlan {
  initial_price: number;
  plan_type: 'one_time' | 'subscription';
}

interface GBTCheckoutCreateParams {
  plan: GBTCheckoutPlan;
  metadata?: Record<string, any>;
  method?: 'stripe' | 'coinflow' | 'cryptapi' | 'dodo';
  project?: string;
  coin?: 'USDT' | 'USDC' | 'USD';
}

interface GBTCheckoutSession {
  success: boolean;
  order_id: string;
  client_order_id?: string | null;
  coin: string;
  amount: number;
  method: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  payment_url?: string;
  checkout_url?: string;
  payment_address?: string;
  expires_at: string;
  [key: string]: any;
}

interface GBTListParams {
  limit?: number;
  starting_after?: string;
  category?: string;
  search?: string;
}

interface GBTRefundParams {
  amount?: number;
  reason?: string;
}

interface GBTDeployCreateParams {
  repo_url: string;
  branch?: string;
  platform?: 'linux' | 'windows' | 'darwin';
  port?: number;
  env?: Record<string, string>;
}

interface GBTDeployResult {
  deploy_id: string;
  status: string;
  [key: string]: any;
}

interface GBTProjectCreateParams {
  name: string;
  repo_url: string;
  description?: string;
  price?: number;
  tags?: string[];
}

interface GBTWebhookUnwrapParams {
  payload: string;
  headers: Record<string, string>;
  secret?: string;
  provider?: 'stripe' | 'cryptapi' | 'coinflow' | 'dodo' | 'gbt';
}

interface GBTAnalyticsParams {
  event: string;
  properties?: Record<string, any>;
}

interface GBTContactParams {
  name: string;
  email: string;
  subject: string;
  message: string;
}

interface GBTRequestOptions {
  body?: any;
  query?: Record<string, any>;
  headers?: Record<string, string>;
}

interface GBTClientConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

interface GBTPaginatedResponse<T> extends Promise<{ data: T[]; has_more?: boolean; next_cursor?: string }> {
  [Symbol.asyncIterator](): AsyncGenerator<T, void, undefined>;
}

declare class CheckoutConfigurationsResource {
  create(params: GBTCheckoutCreateParams, opts?: GBTRequestOptions): Promise<GBTCheckoutSession>;
  retrieve(orderId: string, opts?: GBTRequestOptions): Promise<GBTCheckoutSession>;
}

declare class PaymentsResource {
  list(params?: GBTListParams): GBTPaginatedResponse<any>;
  retrieve(orderId: string): Promise<any>;
  refund(orderId: string, params?: GBTRefundParams): Promise<any>;
}

declare class ProjectsResource {
  list(params?: GBTListParams): GBTPaginatedResponse<any>;
  retrieve(projectId: string): Promise<any>;
  create(params: GBTProjectCreateParams): Promise<any>;
}

declare class DeploymentsResource {
  create(params: GBTDeployCreateParams): Promise<GBTDeployResult>;
  retrieve(deployId: string): Promise<GBTDeployResult>;
  status(deployId: string): Promise<GBTDeployResult>;
  logs(deployId: string, params?: { tail?: number }): Promise<any>;
}

declare class AnalyticsResource {
  track(params: GBTAnalyticsParams): Promise<any>;
}

declare class ContactResource {
  submit(params: GBTContactParams): Promise<any>;
}

declare class WebhooksResource {
  unwrap(params: GBTWebhookUnwrapParams): any;
}

declare class GBT {
  /** GBT constructor reference (self-reference) */
  static GBT: typeof GBT;
  /** GBTError class reference */
  static GBTError: typeof GBTError;
  /** Default export self-reference */
  static default: typeof GBT;

  constructor(config: GBTClientConfig);

  /** @internal */
  _apiKey: string;
  /** @internal */
  _baseUrl: string;
  /** @internal */
  _timeout: number;
  /** @internal */
  _extraHeaders: Record<string, string>;

  readonly checkoutConfigurations: CheckoutConfigurationsResource;
  readonly payments: PaymentsResource;
  readonly projects: ProjectsResource;
  readonly deployments: DeploymentsResource;
  readonly analytics: AnalyticsResource;
  readonly contact: ContactResource;
  readonly webhooks: WebhooksResource;

  request(method: string, path: string, opts?: GBTRequestOptions): Promise<any>;
  health(): Promise<{ ok: boolean }>;
}

export { GBT, GBTError };
export default GBT;
