/**
 * MSW Handlers - centralized exports
 */

import { healthHandlers } from './health'
import { sourcesHandlers } from './sources'
import { validationsHandlers } from './validations'
import { schemasHandlers } from './schemas'
import { profileHandlers } from './profile'
import { historyHandlers } from './history'
import { driftHandlers } from './drift'
import { schedulesHandlers } from './schedules'
import { notificationsHandlers } from './notifications'
import { scanHandlers } from './scan'
import { maskHandlers } from './mask'
import { glossaryHandlers } from './glossary'
import { catalogHandlers } from './catalog'
import { collaborationHandlers } from './collaboration'
import { rulesHandlers } from './rules'
import { validatorsHandlers } from './validators'

export const handlers = [
  ...healthHandlers,
  ...sourcesHandlers,
  ...validationsHandlers,
  ...schemasHandlers,
  ...profileHandlers,
  ...historyHandlers,
  ...driftHandlers,
  ...schedulesHandlers,
  ...notificationsHandlers,
  ...scanHandlers,
  ...maskHandlers,
  ...glossaryHandlers,
  ...catalogHandlers,
  ...collaborationHandlers,
  ...rulesHandlers,
  ...validatorsHandlers,
]
