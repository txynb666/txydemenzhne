"""Teaching scenarios, not measured financial returns. No external price assumptions."""
from decimal import Decimal as D
import json
from pathlib import Path


def calculate():
    # Scope share and adoption are separate; numerator is inquiries, not visits.
    cases = [
        dict(code='A', implementation=26400, build_months='1', scope='0', adoption='0', saved_minutes='0', cash_realization='0', costs=[100,0,200,100,0]),
        dict(code='B', implementation=68000, build_months='2.5', scope='.5', adoption='.6', saved_minutes='2', cash_realization='.4', costs=[300,200,500,300,200]),
        dict(code='C', implementation=156000, build_months='4', scope='.6', adoption='.7', saved_minutes='3', cash_realization='.5', costs=[600,500,1000,500,400]),
        dict(code='D', implementation=268000, build_months='5', scope='.8', adoption='.8', saved_minutes='4', cash_realization='.6', costs=[1000,800,1800,800,600]),
    ]
    results=[]
    for c in cases:
        implementation=D(c['implementation']); months=D(12)-D(c['build_months'])
        operating=D(sum(c['costs'])); scope=D(c['scope']); adoption=D(c['adoption'])
        minutes=D(c['saved_minutes']); realization=D(c['cash_realization'])
        handled=D(180)*D(22)*scope*adoption
        hours=handled*minutes/D(60)
        capacity=hours*D(60)
        cash=capacity*realization
        margin=cash-operating
        total_cost=implementation+months*operating
        benefit=months*cash
        net=benefit-total_cost
        per_daily_query=D(22)*scope*adoption*minutes/D(60)*D(60)*realization
        operating_break_even=operating/per_daily_query if per_daily_query else None
        first_year_break_even=total_cost/(months*per_daily_query) if per_daily_query else None
        result=dict(c, source_status='All forecast assumptions unverified; teaching-only workload source.',
                    operating_months=months, monthly_cost=operating, monthly_handled=handled,
                    monthly_saved_hours=hours, monthly_capacity_value=capacity, monthly_cash=cash,
                    first_year_cost=total_cost, first_year_cash=benefit, first_year_net=net,
                    first_year_roi_percent=net/total_cost*100,
                    payback_months_after_launch=implementation/margin if margin>0 else None,
                    operating_break_even_daily_center_inquiries=operating_break_even,
                    first_year_break_even_daily_center_inquiries=first_year_break_even,
                    no_cash_realization_first_year_net=-total_cost)
        assert benefit-total_cost==net
        assert hours*60==handled*minutes
        results.append(result)
    return results


if __name__=='__main__':
    print(json.dumps(calculate(),ensure_ascii=False,indent=2,default=lambda x: str(x) if isinstance(x,D) else x))
