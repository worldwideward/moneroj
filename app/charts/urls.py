from django.urls import path
from .views import main
from .views import authenticated
from .views import price
from .views import marketcap
from .views import transactions
from .views import issuance
from .views import stock_to_flow
from .views import mining
from .views import social
from .views import subscribers
from .views import adoption

urlpatterns = [
    # Main
    path("", main.index, name="index"),
    path("about/", main.about, name="about"),
    # Price
    path("pricelog/", price.pricelog, name="pricelog"),
    path("pricelin/", price.pricelin, name="pricelin"),
    path("pricesats/", price.pricesats, name="pricesats"),
    path("pricesatslog/", price.pricesatslog, name="pricesatslog"),
    path("fractal/", price.fractal, name="fractal"),
    path("inflationfractal/", price.inflationfractal, name="inflationfractal"),
    path("marketcycle/", price.marketcycle, name="marketcycle"),
    path("golden/", price.golden, name="golden"),
    path("competitors/", price.competitors, name="competitors"),
    path("competitorslin/", price.competitorslin, name="competitorslin"),
    path("competitorssats/", price.competitorssats, name="competitorssats"),
    path("competitorssatslin/", price.competitorssatslin, name="competitorssatslin"),
    path("inflationreturn/", price.inflationreturn, name="inflationreturn"),
    path("bitcoin/", price.bitcoin, name="bitcoin"),
    path("powerlaw/", price.powerlaw, name="powerlaw"),
    path("thermocap/", price.thermocap, name="thermocap"),
    path("sharpe/", price.sharpe, name="sharpe"),
    path("deviation/", price.deviation, name="deviation"),
    # Marketcap
    path("dominance/", marketcap.dominance, name="dominance"),
    path("monerodominance/", marketcap.monerodominance, name="monerodominance"),
    path("privacydominance/", marketcap.privacydominance, name="privacydominance"),
    path("rank/", marketcap.rank, name="rank"),
    path("marketcap/", marketcap.marketcap, name="marketcap"),
    path("privacymarketcap/", marketcap.privacymarketcap, name="privacymarketcap"),
    # Transactions
    path("translin/", transactions.translin, name="translin"),
    path("translog/", transactions.translog, name="translog"),
    path("transmonth/", transactions.transmonth, name="transmonth"),
    path("transcost/", transactions.transcost, name="transcost"),
    path("transcostntv/", transactions.transcostntv, name="transcostntv"),
    path("percentage/", transactions.percentage, name="percentage"),
    path("percentmonth/", transactions.percentmonth, name="percentmonth"),
    path("shielded/", transactions.shielded, name="shielded"),
    path("comptransactions/", transactions.comptransactions, name="comptransactions"),
    path("metcalfesats/", transactions.metcalfesats, name="metcalfesats"),
    path("metcalfeusd/", transactions.metcalfeusd, name="metcalfeusd"),
    path("metcalfesats_deviation/", transactions.metcalfesats_deviation, name="metcalfesats_deviation"),
    path("metcalfe_deviation/", transactions.metcalfe_deviation, name="metcalfe_deviation"),
    path("deviation_tx/", transactions.deviation_tx, name="deviation_tx"),
    path("transactiondominance/", transactions.transactiondominance, name="transactiondominance"),
    # Issuance
    path("coins/", issuance.coins, name="coins"),
    path("extracoins/", issuance.extracoins, name="extracoins"),
    path("inflation/", issuance.inflation, name="inflation"),
    path("tail_emission/", issuance.tail_emission, name="tail_emission"),
    path("compinflation/", issuance.compinflation, name="compinflation"),
    path("dailyemission/", issuance.dailyemission, name="dailyemission"),
    path("dailyemissionntv/", issuance.dailyemissionntv, name="dailyemissionntv"),
    # Stock to Flow
    path("sfmodel/", stock_to_flow.sfmodel, name="sfmodel"),
    path("sfmodellin/", stock_to_flow.sfmodellin, name="sfmodellin"),
    path("sfmultiple/", stock_to_flow.sfmultiple, name="sfmultiple"),
    # Mining
    path("hashrate/", mining.hashrate, name="hashrate"),
    path("hashprice/", mining.hashprice, name="hashprice"),
    path("hashvsprice/", mining.hashvsprice, name="hashvsprice"),
    path("minerrev/", mining.minerrev, name="minerrev"),
    path("minerrevntv/", mining.minerrevntv, name="minerrevntv"),
    path("minerfees/", mining.minerfees, name="minerfees"),
    path("minerfeesntv/", mining.minerfeesntv, name="minerfeesntv"),
    path("miningprofitability/", mining.miningprofitability, name="miningprofitability"),
    path("minerrevcap/", mining.minerrevcap, name="minerrevcap"),
    path("commit/", mining.commit, name="commit"),
    path("commitntv/", mining.commitntv, name="commitntv"),
    path("blocksize/", mining.blocksize, name="blocksize"),
    path("blockchainsize/", mining.blockchainsize, name="blockchainsize"),
    path("transactionsize/", mining.transactionsize, name="transactionsize"),
    path("difficulty/", mining.difficulty, name="difficulty"),
    path("securitybudget/", mining.securitybudget, name="securitybudget"),
    path("efficiency/", mining.efficiency, name="efficiency"),
    path("p2pool_hashrate/", mining.p2pool_hashrate, name="p2pool_hashrate"),
    path("p2pool_dominance/", mining.p2pool_dominance, name="p2pool_dominance"),
    path("p2pool_miners/", mining.p2pool_miners, name="p2pool_miners"),
    path("p2pool_totalblocks/", mining.p2pool_totalblocks, name="p2pool_totalblocks"),
    path("p2pool_totalhashes/", mining.p2pool_totalhashes, name="p2pool_totalhashes"),
    # Social
    path("social/", social.social, name="social"),
    path("social2/", social.social2, name="social2"),
    path("social3/", social.social3, name="social3"),
    path("social4/", social.social4, name="social4"),
    path("social5/", social.social5, name="social5"),
    path("social6/", social.social6, name="social6"),
    path("social7/", social.social7, name="social7"),
    # Subscribers
    path("dread_subscribers/", subscribers.dread_subscribers, name="dread_subscribers"),
    # Adoption
    path("coincards/", adoption.coincards, name="coincards"),
    path("merchants/", adoption.merchants, name="merchants"),
    path("merchants_increase/", adoption.merchants_increase, name="merchants_increase"),
    path("merchants_percentage/", adoption.merchants_percentage, name="merchants_percentage"),
    # Deprecated
    #path("movingaverage/", main.movingaverage, name="movingaverage"),
    #path("withdrawals/", main.withdrawals, name="withdrawals"),
    # URLs to useful functions on charts/main.py
    # Only admins can use these
    path(
        "get_history/<str:symbol>/<str:start_time>/<str:end_time>/",
        authenticated.get_history,
        name="get_history",
    ),
    path(
        "get_complete_history/<str:symbol>/",
        authenticated.get_history,
        name="get_complete_history",
    ),
    path("load_dominance/<str:symbol>/", authenticated.load_dominance, name="load_dominance"),
    path("load_rank/<str:symbol>/", authenticated.load_rank, name="load_rank"),
    path("load_p2pool/", authenticated.load_p2pool, name="load_p2pool"),
    path("populate_database/", authenticated.populate_database, name="populate_database"),
    path("reset/<str:symbol>/", authenticated.reset, name="reset"),
    path("reset_sf_model/", authenticated.reset_sf_model, name="reset_sf_model"),
    path("reset_daily_data/", authenticated.reset_daily_data, name="reset_daily_data"),
    path(
        "update/<str:date_from>/<str:date_to>/",
        authenticated.update_database_admin,
        name="update",
    ),
]
