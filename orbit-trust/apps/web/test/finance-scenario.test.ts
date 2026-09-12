import {test} from 'node:test';
import assert from 'node:assert/strict';
import {financeTotals,defaultFinance} from '../src/lib/finance-scenario.ts';
test('loss and response scenarios retain separate assumptions',()=>{
  const result=financeTotals(defaultFinance);
  assert.equal(result.conditionalLoss,18336000);
  assert.equal(result.responseScenario,133000);
  assert.equal(result.difference,18203000);
  const changed=financeTotals({...defaultFinance,responseDays:30});
  assert.equal(changed.conditionalLoss,result.conditionalLoss);
  assert.equal(changed.responseScenario,805000);
});
test('comparison can be negative; no fabricated positive savings',()=>{
  assert.equal(financeTotals({replacement:0,dailyRevenue:0,days:0,responseCost:500,responseDays:0}).difference,-500);
});
test('invalid and overflowing cost assumptions fail closed',()=>{
  for(const value of [-1,NaN,Infinity])assert.throws(()=>financeTotals({...defaultFinance,days:value}));
  assert.throws(()=>financeTotals({...defaultFinance,dailyRevenue:Number.MAX_VALUE,days:100}));
});
