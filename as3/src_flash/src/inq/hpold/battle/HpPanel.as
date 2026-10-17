package inq.hpold.battle
{
   import flash.display.DisplayObject;
   import flash.display.DisplayObjectContainer;
   import flash.filters.ColorMatrixFilter;
   import flash.utils.Dictionary;

   import inq.hpold.injector.BattleDisplayable;

   public class HpPanel extends BattleDisplayable
   {
      private static const DEFAULT_LT_COLOR:uint = 0x596E4B;
      private static const DEFAULT_MT_COLOR:uint = 0x8B6526;
      private static const DEFAULT_TD_COLOR:uint = 0x3D4658;
      private static const DEFAULT_SPG_COLOR:uint = 0x684940;
      private static const DEFAULT_HEAVY_COLOR:uint = 0x808080;

      private static const HP_COLUMN_OFFSET:Number = 90;
      private static const FALLBACK_INNER_MARGIN:Number = 4;

      private var _data:Dictionary;
      private var _rows:Dictionary;
      private var _iconBaseFilters:Dictionary;
      private var _disposed:Boolean = false;
      private var _showHealth:Boolean = false;
      private var _showHpBars:Boolean = true;
      private var _enemyHpRed:Boolean = false;

      private var _colorizeIcons:Boolean = true;
      private var _colorizeHeavy:Boolean = false;
      private var _ltColor:uint = DEFAULT_LT_COLOR;
      private var _mtColor:uint = DEFAULT_MT_COLOR;
      private var _tdColor:uint = DEFAULT_TD_COLOR;
      private var _spgColor:uint = DEFAULT_SPG_COLOR;
      private var _heavyColor:uint = DEFAULT_HEAVY_COLOR;

      public function HpPanel()
      {
         super();
         name = "inqHpoldPanel";
         _data = new Dictionary();
         _rows = new Dictionary();
         _iconBaseFilters = new Dictionary(true);
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
            row.name = "hpeHealth_" + vehicleID;
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

      private function colorForClass(vehicleClass:String):int
      {
         if (!_colorizeIcons)
            return -1;

         switch (vehicleClass ? vehicleClass.toLowerCase() : "")
         {
            case "lighttank":
               return int(_ltColor);
            case "mediumtank":
               return int(_mtColor);
            case "at-spg":
               return int(_tdColor);
            case "spg":
               return int(_spgColor);
            case "heavytank":
               return _colorizeHeavy ? int(_heavyColor) : -1;
         }
         return -1;
      }

      private function colorFilter(color:uint):ColorMatrixFilter
      {
         var red:Number = ((color >> 16) & 0xFF) / 128.0;
         var green:Number = ((color >> 8) & 0xFF) / 128.0;
         var blue:Number = (color & 0xFF) / 128.0;
         return new ColorMatrixFilter([
            red, 0, 0, 0, 0,
            0, green, 0, 0, 0,
            0, 0, blue, 0, 0,
            0, 0, 0, 1, 0
         ]);
      }

      private function rememberBaseFilters(icon:DisplayObject):Array
      {
         var base:Array = _iconBaseFilters[icon] as Array;
         if (!base)
         {
            base = icon.filters ? icon.filters.slice() : [];
            _iconBaseFilters[icon] = base;
         }
         return base;
      }

      private function restoreIconFilter(icon:DisplayObject):void
      {
         var base:Array = _iconBaseFilters[icon] as Array;
         if (!base)
            return;
         try
         {
            icon.filters = base.slice();
         }
         catch (e:Error)
         {
         }
         delete _iconBaseFilters[icon];
      }

      private function applyIconColor(vehicleID:int):void
      {
         var data:Object = _data[vehicleID];
         if (!data)
            return;

         var item:* = getListItem(vehicleID);
         if (!item)
            return;

         var icon:DisplayObject = member(item, "vehicleIcon") as DisplayObject;
         if (!icon)
            return;

         var color:int = colorForClass(String(data.vehicleClass));
         if (color < 0)
         {
            restoreIconFilter(icon);
            return;
         }

         try
         {
            var filters:Array = rememberBaseFilters(icon).slice();
            filters.push(colorFilter(uint(color)));
            icon.filters = filters;
         }
         catch (e:Error)
         {
         }
      }

      private function applyAllIconColors():void
      {
         if (_disposed)
            return;
         for (var key:* in _data)
            applyIconColor(int(key));
      }

      private function restoreIconColors():void
      {
         var icons:Array = [];
         for (var key:* in _iconBaseFilters)
            icons.push(key);
         for each (var icon:DisplayObject in icons)
         {
            if (icon)
               restoreIconFilter(icon);
         }
         _iconBaseFilters = new Dictionary(true);
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

         applyIconColor(vehicleID);
      }

      public function as_setVehicleHealth(vehicleID:int, currentHealth:int, maxHealth:int, vehicleClass:String = ""):void
      {
         if (_disposed || vehicleID <= 0)
            return;
         _data[vehicleID] = {
            currentHealth: Math.max(0, currentHealth),
            maxHealth: Math.max(0, maxHealth),
            vehicleClass: vehicleClass ? vehicleClass : ""
         };
         applyVehicle(vehicleID);
      }

      public function as_setIconSettings(
         enabled:Boolean,
         colorizeHeavy:Boolean,
         ltColor:uint,
         mtColor:uint,
         tdColor:uint,
         spgColor:uint,
         heavyColor:uint
      ):void
      {
         if (_disposed)
            return;

         if (!enabled && _colorizeIcons)
            restoreIconColors();

         _colorizeIcons = enabled;
         _colorizeHeavy = colorizeHeavy;
         _ltColor = ltColor;
         _mtColor = mtColor;
         _tdColor = tdColor;
         _spgColor = spgColor;
         _heavyColor = heavyColor;

         applyAllIconColors();
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

         restoreIconColors();
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
