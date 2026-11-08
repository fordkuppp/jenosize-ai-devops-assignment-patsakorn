# Gateway and routing

Traffic enters through Envoy Gateway using Gateway API.

## Resources

`GatewayClass/envoy` is cluster-scoped and names a class of service.
`Gateway/external` is named for the traffic tier, not for any tenant — a
second service attaches to the same Gateway with no change to infrastructure.
Applications own only their `HTTPRoute`.

## NodePort and kind

kind has no load balancer, so the Envoy service is a NodePort fixed at 30080
and the kind cluster forwards a host port to it. The port number in
`EnvoyProxy` and the `extraPortMappings` in the Terraform cluster definition
must agree.

## externalTrafficPolicy

The proxy service sets `externalTrafficPolicy: Cluster`, overriding Envoy
Gateway's default of `Local`.

Under `Local`, a node only answers a NodePort if it hosts an endpoint. Host
ports are mapped on the control plane while the proxy pod is scheduled on a
worker, so externally-originated packets arrive at a node with no local
endpoint and are dropped. The symptom is a connection timeout rather than a
refusal, and traffic originating inside the node still works — which makes
the NodePort look healthy while being unreachable from outside.

Client IP preservation is meaningless behind a kind port mapping, so nothing
is lost by using `Cluster`.

## Rate limiting

Rate limiting is an Envoy `BackendTrafficPolicy` attached to the HTTPRoute:
60 requests per minute, local (per-proxy) rather than global. Typed and
schema-validated configuration rather than an annotation string. The same
policy carries the circuit breaker settings.
