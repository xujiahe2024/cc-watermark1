#!/bin/bash

namespaces=$(kubectl get namespaces -o jsonpath="{.items[*].metadata.name}")

for namespace in $namespaces; do
    echo "Namespace: $namespace"
   
    pods=$(kubectl get pods -n $namespace -o jsonpath="{.items[*].metadata.name}")
    for pod in $pods; do
        echo "  Pod: $pod"
        
        service_account=$(kubectl get pod $pod -n $namespace -o jsonpath="{.spec.serviceAccountName}")
        echo "    Service Account: $service_account"
        #RoleBinding 和 ClusterRoleBinding
        role_bindings=$(kubectl get rolebindings -n $namespace -o json | jq -r ".items[] | select(.subjects[].name==\"$service_account\") | .metadata.name")
        cluster_role_bindings=$(kubectl get clusterrolebindings -o json | jq -r ".items[] | select(.subjects[].name==\"$service_account\") | .metadata.name")
        for role_binding in $role_bindings; do
            echo "      RoleBinding: $role_binding"
            kubectl describe rolebinding $role_binding -n $namespace | grep -A 1 "RoleRef"
        done
        for cluster_role_binding in $cluster_role_bindings; do
            echo "      ClusterRoleBinding: $cluster_role_binding"
            kubectl describe clusterrolebinding $cluster_role_binding | grep -A 1 "RoleRef"
        done
    done
done
