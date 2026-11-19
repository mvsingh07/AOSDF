---
concepts: [aws-region-az, aws-iam, vpc-subnets, cloud-compute-storage-choice]
concept_category: DevOps/Infra
difficulty: fundamental
prerequisites: []
interview_angle: >
  Explain the workload requirement before choosing EC2, ECS, or Lambda; show where
  IAM, network reachability, and availability boundaries sit in the design.
built_at: framework-learning-roadmap
diagram: true
---

# AWS Architecture Primitives

## Definition

A Region is a geographic deployment choice; Availability Zones provide separate failure
locations within a Region. IAM controls which principal can perform which action on a
resource. A VPC, subnet, route table, and security group shape network reachability.
EC2 offers OS control, ECS runs containers, and Lambda handles event-driven functions
within its runtime limits. S3 stores objects; RDS serves relational transactions; the
right choice follows workload and operating constraints.

## Example

A Comms API can sit behind a public load balancer while its ECS tasks and RDS database
run in private subnets across AZs. A worker role can receive from one SQS queue and read
one provider secret. The database accepts traffic from the application security group,
not from arbitrary internet addresses.

## Diagram

```aosdf-diagram
Internet ──▶ public ALB ──▶ private ECS ──▶ private RDS
                              │ IAM role
                              ├──▶ SQS queue
                              └──▶ one provider secret
```

## Use It While Building

Draw inbound and outbound paths, the resource principal for each call, and the failure
domain each AZ or Region choice addresses. Review operational excellence, security,
reliability, performance, cost, and sustainability together.

## Sources

- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- [Amazon VPC User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
