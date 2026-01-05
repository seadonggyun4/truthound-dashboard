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
]
