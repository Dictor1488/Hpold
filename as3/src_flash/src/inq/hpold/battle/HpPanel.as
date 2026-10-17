package inq.hpold.battle
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.utils.Dictionary;

   import inq.hpold.injector.BattleDisplayable;

   public class HpPanel extends BattleDisplayable
   {
      private static const HP_COLUMN_OFFSET:Number = 90;
      private static const FALLBACK_INNER_MARGIN:Number = 4;

      private var _data:Dictionary;
      private var _rows:Dictionary;
      private var _disposed:Boolean = false;
      private var _showHealth:Boolean = false;
      private var _showHpBars:Boolean = true;
      private var _enemyHpRed:Boolean = false;

      public function HpPanel()
      {
         super();
         name = "inqHpoldPanel";
         _data = new Dictionary();
         _rows = new Dictionary();
      }

      private function member(target:*, name:String):*
      {
         if (!target)
            return null;
         try
         {
            return target[name];
         }
         catch (e:Error)
         {
         }
         return null;
      }

      private function resolvePlayersPanel():*
      {
         var page:* = battlePage;
         if (!page)
            return null;

         var panel:* = member(page, "playersPanel");
         if (panel)
            return panel;

         panel = member(page, "epicRandomPlayersPanel");
         if (panel)
            return panel;

         return null;
      }

      private function holder(list:*, vehicleID:int):*
      {
         if (!list)
            return null;
         try
         {
            return list.getHolderByVehicleID(vehicleID);
         }
         catch (e:Error)
         {
         }
         try
         {
            return list.getHolderByVehicleId(vehicleID);
         }
         catch (e2:Error)
         {
         }
         return null;
      }

      private function listItemFromHolder(value:*):*
      {
         if (!value)
            return null;
         try
         {
            return value.getListItem();
         }
         catch (e:Error)
         {
         }
         var item:* = member(value, "_listItem");
         if (item)
            return item;
         return member(value, "listItem");
      }

      private function getListItem(vehicleID:int):*
      {
         var panel:* = resolvePlayersPanel();
         if (!panel)
            return null;

         var value:* = holder(member(panel, "listLeft"), vehicleID);
         if (value)
            return listItemFromHolder(value);

         value = holder(member(panel, "listRight"), vehicleID);
         if (value)
            return listItemFromHolder(value);

         return null;
      }

      private function isEnemy(vehicleID:int):Boolean
      {
         var panel:* = resolvePlayersPanel();
         if (!panel)
            return false;
         return holder(member(panel, "listRight"), vehicleID) != null;
      }

      private function ensureRow(vehicleID:int, item:*):HealthRow
      {
         var row:HealthRow = _rows[vehicleID] as HealthRow;
         if (!row)
         {
            row = new HealthRow();
            row.name = "inqHpoldHealth_" + vehicleID;
            row.visible = false;
            row.setShowBar(_showHpBars);
            row.setEnemyHpRed(_enemyHpRed);
            _rows[vehicleID] = row;
         }

         if (row.parent != item && item is DisplayObjectContainer)
         {
            if (row.parent)
               row.parent.removeChild(row);
            DisplayObjectContainer(item).addChild(row);
         }
         return row;
      }

      private function itemIsVisible(item:*):Boolean
      {
         if (!item)
            return false;
         try
         {
            return Boolean(item.visible);
         }
         catch (e:Error)
         {
         }
         return true;
      }

      private function positionRow(vehicleID:int, item:*, row:HealthRow, enemy:Boolean):void
      {
         if (!item || !row)
            return;

         var icon:DisplayObject = member(item, "vehicleIcon") as DisplayObject;
         var vehicleTF:DisplayObject = member(item, "vehicleTF") as DisplayObject;
         var anchor:DisplayObject = icon ? icon : vehicleTF;
         var width:Number = row.contentWidth;

         if (anchor)
         {
            row.x = Math.round(
               enemy
                  ? anchor.x - HP_COLUMN_OFFSET - width
                  : anchor.x + HP_COLUMN_OFFSET
            );
            row.y = Math.round(anchor.y);
         }
         else
         {
            var itemWidth:Number = 300;
            try
            {
               itemWidth = Number(item.width);
            }
            catch (e:Error)
            {
            }
            row.x = Math.round(
               enemy
                  ? FALLBACK_INNER_MARGIN
                  : Math.max(
                       FALLBACK_INNER_MARGIN,
                       itemWidth - width - FALLBACK_INNER_MARGIN
                    )
            );
            row.y = 0;
         }

         var data:Object = _data[vehicleID];
         row.visible = _showHealth && itemIsVisible(item) && data != null && int(data.maxHealth) > 0;
      }

      private function refreshRowVisibility():void
      {
         for (var key:* in _rows)
         {
            var vehicleID:int = int(key);
            var row:HealthRow = _rows[key] as HealthRow;
            if (!row)
               continue;

            var item:* = getListItem(vehicleID);
            var data:Object = _data[vehicleID];
            row.visible = _showHealth && itemIsVisible(item) && data != null && int(data.maxHealth) > 0;
         }
      }

      private function applyVehicle(vehicleID:int):void
      {
         var data:Object = _data[vehicleID];
         if (!data)
            return;

         var item:* = getListItem(vehicleID);
         var row:HealthRow = _rows[vehicleID] as HealthRow;
         if (!item)
         {
            if (row)
               row.visible = false;
            return;
         }

         var enemy:Boolean = isEnemy(vehicleID);
         row = ensureRow(vehicleID, item);
         row.setShowBar(_showHpBars);
         row.setEnemyHpRed(_enemyHpRed);
         row.updateHealth(int(data.currentHealth), int(data.maxHealth), enemy);
         positionRow(vehicleID, item, row, enemy);

      }

      public function as_setVehicleHealth(vehicleID:int, currentHealth:int, maxHealth:int, vehicleClass:String = ""):void
      {
         if (_disposed || vehicleID <= 0)
            return;
         _data[vehicleID] = {
            currentHealth: Math.max(0, currentHealth),
            maxHealth: Math.max(0, maxHealth),
            vehicleClass: ""
         };
         applyVehicle(vehicleID);
      }

      public function as_setIconSettings(
         enabled:Boolean, colorizeHeavy:Boolean, ltColor:uint, mtColor:uint,
         tdColor:uint, spgColor:uint, heavyColor:uint
      ):void
      {
         // Compatibility hook only: never recolor or draw tank icons.
      }

      public function as_setDisplaySettings(showHpBars:Boolean, enemyHpRed:Boolean):void
      {
         if (_disposed)
            return;
         _showHpBars = showHpBars;
         _enemyHpRed = enemyHpRed;
         for each (var row:HealthRow in _rows)
         {
            if (row)
            {
               row.setShowBar(_showHpBars);
               row.setEnemyHpRed(_enemyHpRed);
            }
         }
         as_refreshAll();
      }

      public function as_setVisibility(value:Boolean):void
      {
         if (_disposed)
            return;

         _showHealth = value;
         if (_showHealth)
            as_refreshAll();
         else
            refreshRowVisibility();
      }

      public function as_refreshAll():void
      {
         if (_disposed)
            return;
         for (var key:* in _data)
            applyVehicle(int(key));
      }

      public function as_clear():void
      {
         _showHealth = false;

         for each (var row:HealthRow in _rows)
         {
            if (row && row.parent)
               row.parent.removeChild(row);
         }

         _rows = new Dictionary();
         _data = new Dictionary();
      }

      override protected function onDispose():void
      {
         _disposed = true;
         as_clear();
         super.onDispose();
      }
   }
}
