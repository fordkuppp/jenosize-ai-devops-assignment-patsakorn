# dev — one task per service, smallest viable instance classes.
#
# TODO (yours): call the modules.
#
#   module "network" { source = "../../modules/network" ... }
#   module "data"    { source = "../../modules/data"    ... }   # rds + secrets
#   module "compute" { source = "../../modules/compute" ... }   # ecr + ecs + alb
#   module "observability" { source = "../../modules/observability" ... }
#
# The difference between this file and envs/prod should be *values*, not
# structure. If prod needs a resource dev does not have, that is worth a line
# in the README explaining why.
