export interface FinanceInputs {replacement:number;dailyRevenue:number;days:number;responseCost:number;responseDays:number}
export const defaultFinance:FinanceInputs={replacement:18000000,dailyRevenue:24000,days:14,responseCost:85000,responseDays:2};
export function financeTotals(input:FinanceInputs) {
  if(Object.values(input).some(v=>!Number.isFinite(v)||v<0))throw new Error('Enter a finite, nonnegative value for every assumption.');
  const service=input.dailyRevenue*input.days;
  const conditionalLoss=input.replacement+service;
  const responseScenario=input.responseCost+input.dailyRevenue*input.responseDays;
  if(![service,conditionalLoss,responseScenario].every(Number.isFinite))throw new Error('These assumptions exceed the supported numeric range.');
  return {service,conditionalLoss,responseScenario,difference:conditionalLoss-responseScenario};
}
