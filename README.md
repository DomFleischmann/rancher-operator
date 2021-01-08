# Rancher Operator **WORK IN PROGRESS**

This is the result of an initial spike to test the viability of a Charm for Rancher.
**The current charm does not work correctly**. It is able to deploy the rancher service
but fails during deployment. Nevertheless the other Rancher resources are deployed
successfully.

## Testing the Charm

```
# Install microk8s and enabel addons
sudo snap install microk8s --classic
microk8s.enable storage dns rbac ingress helm3

# Cert manager instructions taken from offial Rancher Documentation
microk8s.kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.0.4/cert-manager.crds.yaml
microk8s.kubectl create namespace cert-manager
microk8s.helm3 repo add jetstack https://charts.jetstack.io
microk8s.helm3 repo update
microk8s.helm3 install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --version v1.0.4

# Bootstrap microk8s with juju
sudo snap install juju --classic
juju bootstrap microk8s
juju add-model rancher

# Build and deploy Rancher charm
charmcraft build
juju deploy ./rancher.charm --resource rancher-image=rancher/rancher
```
