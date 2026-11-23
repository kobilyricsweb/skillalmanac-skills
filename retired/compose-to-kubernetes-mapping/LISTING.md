# Compose to Kubernetes mapping

## One line

Maps the services of a Docker Compose file to Kubernetes Deployment, Service and PersistentVolumeClaim skeletons, with a row for every key and a gap list for everything that does not translate.

## What it does

The skill reads one Compose file and walks it service by service. Each key under a service gets one row in a table. The row names the Kubernetes field the value would land in, or says NO-EQUIVALENT when there is no field. Ports follow a fixed table, so `"8080:80"` becomes a Service port of 8080 aimed at container port 80, while a bare `"80"` produces no Service. Environment values are checked with a secret test. A name such as POSTGRES_PASSWORD, or a URL that carries credentials, is written as a secretKeyRef and its value is replaced by `<redacted>` everywhere in the output.

Named volumes become PersistentVolumeClaim blocks whose size and access mode are placeholders the user must fill. Bind mounts, depends_on and build are listed as gaps. The output ends with counts, a numbered gap list and, when anything is missing, a list of open questions.

The skill does not invent images, replica counts, resource limits or credentials. Where the file is silent, the output keeps a visible placeholder such as `<image-required>`.

## When to use

Use it when a team has a Compose file for a service set and wants a first Kubernetes draft that shows, line by line, what carried over and what needs a human decision. It suits a small stack of two to ten services that share a volume or two.

## When not to use

Do not use it for Helm charts, cluster sizing, image builds or applying manifests to a cluster. It does not decide health probes, network policy or ingress. It does not read `env_file` contents or `.env` files. Files longer than 300 lines are refused and should be split by service first.

## Requirements

A text-capable agent and the Compose file pasted as text. No tools, no network and no scripts are needed.

## Example

Input (25 lines, three services, one named volume, two depends_on entries). The secret values are test values:

```
services:
  web:
    image: nginx:1.25
    ports:
      - "8080:80"
    environment:
      APP_ENV: production
    depends_on: [api]
  api:
    build: ./api
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgres://app:example-value-1@db:5432/app
    volumes:
      - app-data:/var/lib/app
    depends_on: [db]
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: example-value-2
    volumes:
      - app-data:/var/lib/postgresql/data
volumes:
  app-data:
```

Output:

```
# Compose to Kubernetes mapping: unnamed
Status: partial

## Counts
| Metric | Value |
|---|---|
| Services | 3 |
| Service keys read | 12 |
| MAPPED | 5 |
| PARTIAL | 4 |
| NO-EQUIVALENT | 3 |
| Gap items | 7 |

## Service mapping
### web
| Compose key | Value in file | Kubernetes target | Status | Note |
|---|---|---|---|---|
| image | nginx:1.25 | containers[0].image | MAPPED | |
| ports | "8080:80" | Service port 8080, targetPort 80; containers[0].ports containerPort 80 | MAPPED | host:container form |
| environment | APP_ENV: production | containers[0].env | MAPPED | 1 literal, 0 secret |
| depends_on | [api] | none | NO-EQUIVALENT | no start order field |

### api
| Compose key | Value in file | Kubernetes target | Status | Note |
|---|---|---|---|---|
| build | ./api | none | NO-EQUIVALENT | no image key; containers[0].image is <image-required> |
| ports | "5000:5000" | Service port 5000, targetPort 5000; containerPort 5000 | MAPPED | host:container form |
| environment | DATABASE_URL: <redacted> | containers[0].env valueFrom.secretKeyRef api-secrets/DATABASE_URL | PARTIAL | 1 secret (URL with credentials) |
| volumes | app-data:/var/lib/app | volumeMount app-data at /var/lib/app; PVC app-data | PARTIAL | named, declared; size and access mode required |
| depends_on | [db] | none | NO-EQUIVALENT | no start order field |

### db
| Compose key | Value in file | Kubernetes target | Status | Note |
|---|---|---|---|---|
| image | postgres:16 | containers[0].image | MAPPED | |
| environment | POSTGRES_PASSWORD: <redacted> | containers[0].env valueFrom.secretKeyRef db-secrets/POSTGRES_PASSWORD | PARTIAL | 1 secret (name contains PASSWORD) |
| volumes | app-data:/var/lib/postgresql/data | volumeMount app-data; PVC app-data (shared with api) | PARTIAL | access mode required |

## Skeleton

### web Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.25
          ports:
            - containerPort: 80
          env:
            - name: APP_ENV
              value: production
```

### web Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
    - port: 8080
      targetPort: 80
```

### api Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: <image-required>
          ports:
            - containerPort: 5000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: DATABASE_URL
          volumeMounts:
            - name: app-data
              mountPath: /var/lib/app
      volumes:
        - name: app-data
          persistentVolumeClaim:
            claimName: app-data
```

### api Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 5000
      targetPort: 5000
```

### db Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: db
spec:
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
        - name: db
          image: postgres:16
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secrets
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: app-data
              mountPath: /var/lib/postgresql/data
      volumes:
        - name: app-data
          persistentVolumeClaim:
            claimName: app-data
```

### app-data PersistentVolumeClaim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - <access-mode-required>
  resources:
    requests:
      storage: <size-required>
```

## Gap list
| ID | Service | Compose key | Status | Reason |
|---|---|---|---|---|
| G1 | web | depends_on | NO-EQUIVALENT | Kubernetes has no start order field; use an initContainer or readinessProbe by hand |
| G2 | api | build | NO-EQUIVALENT | no image is built or pushed by this mapping |
| G3 | api | environment | PARTIAL | DATABASE_URL is a secret; create Secret api-secrets outside this output |
| G4 | api | volumes | PARTIAL | claim size and access mode required |
| G5 | api | depends_on | NO-EQUIVALENT | same as G1 |
| G6 | db | environment | PARTIAL | POSTGRES_PASSWORD is a secret; create Secret db-secrets outside this output |
| G7 | db | volumes | PARTIAL | app-data is also mounted by api; access mode required |

## Open questions
1. Which image should the api service run? The file has `build: ./api` and no `image` key.
2. What storage size should the app-data claim request?
3. Which access mode should app-data use, given that api and db both mount it?
```

## Limits

The skill maps keys with a fixed table. It does not check whether an image tag exists, whether the Kubernetes API version in the skeleton is current for a given cluster, or whether a value is valid for the field it lands in. The secret test is a name and URL heuristic, so a secret with an unusual name passes as a literal, and a harmless value with a matching name is redacted. It does not validate port conflicts, volume names, or the behavior of `restart` on a real cluster. It does not verify security posture: a Docker socket mount is flagged as a host-access risk, not assessed. Output is a draft for review by someone who knows the target cluster.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
