const _KRoWd9wBIIBMv7WbjZIE = require('../unmerged_dictionary/catalog.json');
const _Y7oZmA5LmDtL3JEgsUPM = require('../unmerged_dictionary/collaboration.json');
const _vCCVBp8kCGmTeHIzCwhA = require('../unmerged_dictionary/common.json');
const _qVbNqQq6pwYPWgya2g20 = require('../unmerged_dictionary/dashboard.json');
const _OOww4DugJtZvnuznqu1l = require('../unmerged_dictionary/demo.json');
const _EqtELq9jioJ880u655Pn = require('../unmerged_dictionary/drift.json');
const _Ua3ZVftySEXFAxqrkJjk = require('../unmerged_dictionary/errors.json');
const _rzrtvdsW6MA7HG6MZiqM = require('../unmerged_dictionary/glossary.json');
const _CS4ZBheaDXved5UeTYiT = require('../unmerged_dictionary/nav.json');
const _sg3ZrUmJodT8xcUfcD8d = require('../unmerged_dictionary/notifications.json');
const _xgn6YfRH8hT7OqP2mxRN = require('../unmerged_dictionary/schedules.json');
const _ZOAdeBI7bXfBrnKogJeu = require('../unmerged_dictionary/settings.json');
const _mluQYzldy0M4oRk4zK6X = require('../unmerged_dictionary/sources.json');
const _Tk2hZa9MyMPkZgDZ7y4d = require('../unmerged_dictionary/validation.json');

const dictionaries = {
  "catalog": _KRoWd9wBIIBMv7WbjZIE,
  "collaboration": _Y7oZmA5LmDtL3JEgsUPM,
  "common": _vCCVBp8kCGmTeHIzCwhA,
  "dashboard": _qVbNqQq6pwYPWgya2g20,
  "demo": _OOww4DugJtZvnuznqu1l,
  "drift": _EqtELq9jioJ880u655Pn,
  "errors": _Ua3ZVftySEXFAxqrkJjk,
  "glossary": _rzrtvdsW6MA7HG6MZiqM,
  "nav": _CS4ZBheaDXved5UeTYiT,
  "notifications": _sg3ZrUmJodT8xcUfcD8d,
  "schedules": _xgn6YfRH8hT7OqP2mxRN,
  "settings": _ZOAdeBI7bXfBrnKogJeu,
  "sources": _mluQYzldy0M4oRk4zK6X,
  "validation": _Tk2hZa9MyMPkZgDZ7y4d
};
const getUnmergedDictionaries = () => dictionaries;

module.exports.getUnmergedDictionaries = getUnmergedDictionaries;
module.exports = dictionaries;
